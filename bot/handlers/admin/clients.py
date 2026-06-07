"""Admin client management: list, view, create, extend, delete, reset, links, QR, quota."""
from __future__ import annotations

import math
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestUsers,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api import XUIClient, XUIError
from bot.api.models import Client, ClientCreate
from bot.config import Settings
from bot.i18n import t
from bot.keyboards.admin import (
    back_home,
    client_card,
    clients_list,
    confirm_create,
    confirm_delete,
    find_prompt_kb,
    inbound_filter,
    inbound_picker,
    ip_log_kb,
    quick_days,
    quick_iplimit,
    quick_quota,
)
from bot.keyboards.callbacks import ClientCB, ConfirmCB, InbPickCB, MenuCB, PageCB, QuickPickCB
from bot.middlewares.filters import IsAdmin
from bot.states import (
    CreateClient,
    ExtendClient,
    FindClient,
    SetExpiry,
    SetIpLimit,
    SetQuota,
    SetTgId,
)
from bot.utils.formatting import (
    compact_bytes,
    esc,
    extract_last_online,
    fmt_expiry_card,
    fmt_ips,
    fmt_quota_card,
    make_qr_png,
)

router = Router(name="admin-clients")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

PAGE_SIZE = 8


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_client(
    c: Client,
    lang: str = "en",
    *,
    tz: ZoneInfo | None = None,
    inbound_remarks: list[str] | None = None,
    is_online: bool | None = None,
    last_online_str: str | None = None,
) -> str:
    inbounds_label = (
        ", ".join(inbound_remarks) if inbound_remarks
        else ", ".join(f"#{i}" for i in c.inbound_ids) or "—"
    )
    enabled_mark = t("mark_yes", lang) if c.enable else t("mark_no", lang)
    now_ms = int(time.time() * 1000)
    is_active = c.enable and (c.expiry_time == 0 or c.expiry_time > now_ms)
    active_mark = t("mark_yes", lang) if is_active else t("mark_no", lang)
    quota_label = fmt_quota_card(c.total_gb, c.reset)
    expiry_label = fmt_expiry_card(c.expiry_time, c.reset, tz)
    refresh_ts = datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        t("card_email", lang, v=esc(c.email)),
        t("card_inbounds", lang, v=inbounds_label),
        t("card_enabled", lang, v=enabled_mark),
    ]
    if is_online is not None:
        conn = t("mark_online", lang) if is_online else t("mark_offline", lang)
        lines.append(t("card_connection", lang, v=conn))
    if last_online_str:
        lines.append(t("card_last_online", lang, v=last_online_str))
    lines += [
        t("card_active", lang, v=active_mark),
        t("card_expire", lang, v=expiry_label),
        t("card_upload", lang, v=compact_bytes(c.up)),
        t("card_download", lang, v=compact_bytes(c.down)),
        t("card_total", lang, used=compact_bytes(c.up + c.down), quota=quota_label),
        "",
        t("refreshed_on", lang, v=refresh_ts),
    ]
    return "\n".join(lines)


async def _fetch_render_extras(
    api: XUIClient, client: Client, tz: ZoneInfo | None = None
) -> tuple[list[str] | None, bool | None, str | None]:
    inbound_remarks: list[str] | None = None
    is_online: bool | None = None
    last_online_str: str | None = None

    try:
        options = await api.inbound_options()
        remark_map = {o.id: (o.remark or o.protocol) for o in options}
        remarks = [remark_map.get(i, f"#{i}") for i in client.inbound_ids]
        inbound_remarks = remarks or None
    except Exception:
        pass

    try:
        online = await api.online_clients()
        is_online = client.email in online
    except Exception:
        pass

    if client.last_online > 0:
        try:
            dt = datetime.fromtimestamp(client.last_online / 1000, tz=tz)
            last_online_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            pass

    if not last_online_str:
        try:
            raw_ips = await api.client_ips(client.email)
            last_online_str = extract_last_online(raw_ips, tz)
        except Exception:
            pass

    return inbound_remarks, is_online, last_online_str


async def show_card(
    query: CallbackQuery, api: XUIClient, email: str, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(
            t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang)
        )
        return
    inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, client, tz)
    await query.message.edit_text(
        render_client(client, lang, tz=tz, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
        reply_markup=client_card(client, lang),
    )


# --------------------------------------------------------------------------- #
# List + view
# --------------------------------------------------------------------------- #
async def _render_page(
    api: XUIClient, page: int, inbound_id: int = -1, lang: str = "en"
) -> tuple[str, list[Client], int]:
    all_clients = sorted(await api.list_clients(), key=lambda c: c.id)
    if inbound_id != -1:
        clients = [c for c in all_clients if inbound_id in c.inbound_ids]
        filter_label = t("clients_filter_label", lang, v=inbound_id)
    else:
        clients = all_clients
        filter_label = ""
    pages = max(1, math.ceil(len(clients) / PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    chunk = clients[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    text = t("clients_title", lang, filter=filter_label, count=len(clients))
    return text, chunk, pages


@router.callback_query(MenuCB.filter(F.action == "clients"))
async def cb_clients(query: CallbackQuery, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer(t("loading", lang))
    try:
        options = await api.inbound_options()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    await query.message.edit_text(
        t("clients_filter_prompt", lang),
        reply_markup=inbound_filter(options, lang),
    )


@router.callback_query(PageCB.filter(F.target == "clients"))
async def cb_clients_page(query: CallbackQuery, callback_data: PageCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer()
    try:
        text, chunk, pages = await _render_page(api, callback_data.page, callback_data.inbound_id, lang)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    await query.message.edit_text(
        text,
        reply_markup=clients_list(chunk, callback_data.page, pages, callback_data.inbound_id, lang),
    )


@router.callback_query(ClientCB.filter(F.action == "view"))
async def cb_view(query: CallbackQuery, callback_data: ClientCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer()
    await show_card(query, api, callback_data.email, lang, tz)


@router.callback_query(ClientCB.filter(F.action == "refresh"))
async def cb_refresh(query: CallbackQuery, callback_data: ClientCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer(t("loading", lang))
    await show_card(query, api, callback_data.email, lang, tz)


# --------------------------------------------------------------------------- #
# Find by email
# --------------------------------------------------------------------------- #
def _pick_list_kb(clients: list[Client]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in clients:
        builder.button(text=c.email, callback_data=ClientCB(action="view", email=c.email))
    builder.adjust(1)
    return builder.as_markup()


async def _search_and_show(message: Message, api: XUIClient, search: str, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    try:
        clients, filtered = await api.search_clients(search, page_size=25)
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return

    if filtered == 0:
        await message.answer(
            t("find_no_match", lang, q=esc(search)), reply_markup=back_home(lang)
        )
        return

    if filtered > 25:
        await message.answer(t("find_many_matches", lang, count=filtered, q=esc(search)))
        return

    if filtered == 1:
        client = await api.get_client(clients[0].email)
        if client is None:
            await message.answer(
                t("client_not_found", lang, email=esc(clients[0].email)), reply_markup=back_home(lang)
            )
            return
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, client, tz)
        await message.answer(
            render_client(client, lang, tz=tz, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(client, lang),
        )
        return

    await message.answer(
        t("find_pick_result", lang, count=filtered, q=esc(search)),
        reply_markup=_pick_list_kb(clients),
    )


@router.callback_query(MenuCB.filter(F.action == "find"))
async def cb_find(query: CallbackQuery, state: FSMContext, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await state.set_state(FindClient.email)
    await query.message.edit_text(t("find_prompt", lang), reply_markup=find_prompt_kb(lang))
    await query.answer()


@router.message(Command("find"))
async def cmd_find(message: Message, state: FSMContext, lang: str = "en") -> None:
    await state.set_state(FindClient.email)
    await message.answer(t("find_prompt", lang), reply_markup=find_prompt_kb(lang))


@router.message(FindClient.email, F.text)
async def find_email(message: Message, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await state.clear()
    try:
        await message.delete()
    except Exception:
        pass
    await _search_and_show(message, api, message.text.strip(), lang, tz)


# --------------------------------------------------------------------------- #
# Per-client actions: reset, toggle, links, IPs, sub, QR
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "reset"))
async def cb_reset(query: CallbackQuery, callback_data: ClientCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    try:
        await api.reset_client_traffic(callback_data.email)
        await query.answer(t("traffic_reset_done", lang))
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
    await show_card(query, api, callback_data.email, lang, tz)


@router.callback_query(ClientCB.filter(F.action == "toggle"))
async def cb_toggle(query: CallbackQuery, callback_data: ClientCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    client = await api.get_client(callback_data.email)
    if client is None:
        await query.answer(t("not_found_alert", lang), show_alert=True)
        return
    payload = client.to_update_payload(enable=not client.enable)
    try:
        await api.update_client(client.email, payload)
        await query.answer(t("updated_ok", lang))
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
    await show_card(query, api, callback_data.email, lang, tz)


@router.callback_query(ClientCB.filter(F.action == "links"))
async def cb_links(query: CallbackQuery, callback_data: ClientCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer(t("loading", lang))
    try:
        links = await api.client_links(callback_data.email)
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
        return
    if not links:
        body = t("no_links", lang)
    else:
        body = "\n\n".join(f"<code>{u}</code>" for u in links)
    await query.message.edit_text(
        f"{t('links_title', lang, email=esc(callback_data.email))}\n\n{body}",
        reply_markup=back_home(lang),
    )


@router.callback_query(ClientCB.filter(F.action == "ips"))
async def cb_ips(query: CallbackQuery, callback_data: ClientCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer(t("loading", lang))
    try:
        raw = await api.client_ips(callback_data.email)
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
        return
    body = fmt_ips(raw, tz)
    await query.message.edit_text(
        f"{t('ips_title', lang, email=esc(callback_data.email))}\n\n{body}",
        reply_markup=ip_log_kb(callback_data.email, lang),
    )


@router.callback_query(ClientCB.filter(F.action == "clearips"))
async def cb_clearips(query: CallbackQuery, callback_data: ClientCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    try:
        await api.clear_client_ips(callback_data.email)
        await query.answer(t("ip_list_cleared", lang))
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
    await show_card(query, api, callback_data.email, lang, tz)


@router.callback_query(ClientCB.filter(F.action == "sublinks"))
async def cb_sublinks(
    query: CallbackQuery, callback_data: ClientCB, api: XUIClient, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    await query.answer(t("loading", lang))
    client = await api.get_client(callback_data.email)
    if client is None:
        await query.message.edit_text(
            t("client_not_found", lang, email=esc(callback_data.email)),
            reply_markup=back_home(lang),
        )
        return

    parts: list[str] = []
    if client.sub_id and settings.sub_base_url:
        sub_url = settings.sub_base_url.rstrip("/") + "/" + client.sub_id
        parts.append(f"{t('sub_url_label', lang)}\n<code>{sub_url}</code>")
    else:
        parts.append(t("no_sub_url", lang))

    await query.message.edit_text(
        f"{t('sublinks_title', lang, email=esc(callback_data.email))}\n\n" + "\n\n".join(parts),
        reply_markup=back_home(lang),
    )


@router.callback_query(ClientCB.filter(F.action == "qr"))
async def cb_qr(
    query: CallbackQuery, callback_data: ClientCB, api: XUIClient, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    await query.answer(t("qr_generating", lang))
    client = await api.get_client(callback_data.email)
    if client is None:
        await query.message.edit_text(
            t("client_not_found", lang, email=esc(callback_data.email)),
            reply_markup=back_home(lang),
        )
        return

    sent_any = False

    if client.sub_id and settings.sub_base_url:
        sub_url = settings.sub_base_url.rstrip("/") + "/" + client.sub_id
        png = make_qr_png(sub_url)
        file = BufferedInputFile(png, filename=f"{callback_data.email}_sub.png")
        await query.message.answer_document(
            file, caption=t("qr_sub_caption", lang, email=esc(callback_data.email))
        )
        sent_any = True

    try:
        links = await api.client_links(callback_data.email)
        for i, link in enumerate(links[:5], 1):
            png = make_qr_png(link)
            file = BufferedInputFile(png, filename=f"{callback_data.email}_link{i}.png")
            await query.message.answer_document(
                file, caption=t("qr_config_caption", lang, n=i, email=esc(callback_data.email))
            )
            sent_any = True
    except XUIError:
        pass

    if not sent_any:
        await query.message.edit_text(t("qr_no_data", lang), reply_markup=back_home(lang))
    else:
        await query.message.answer(t("qr_done", lang), reply_markup=back_home(lang))


# --------------------------------------------------------------------------- #
# Delete (with confirmation)
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "del"))
async def cb_del(query: CallbackQuery, callback_data: ClientCB, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.message.edit_text(
        t("del_confirm", lang, email=esc(callback_data.email)),
        reply_markup=confirm_delete(callback_data.email, lang),
    )
    await query.answer()


@router.callback_query(ConfirmCB.filter((F.action == "yes") & (F.scope == "del")))
async def cb_del_confirm(query: CallbackQuery, callback_data: ConfirmCB, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    try:
        await api.delete_client(callback_data.arg)
        await query.answer(t("deleted_ok", lang))
        await query.message.edit_text(
            t("del_done", lang, email=esc(callback_data.arg)), reply_markup=back_home(lang)
        )
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)


# --------------------------------------------------------------------------- #
# Set TG ID — native Telegram user picker + numeric text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "set_tgid"))
async def cb_set_tgid(
    query: CallbackQuery, callback_data: ClientCB, state: FSMContext, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    email = callback_data.email
    await state.set_state(SetTgId.waiting)
    await state.update_data(email=email)
    await query.answer()

    picker_btn = KeyboardButton(
        text=t("btn_pick_tg_user", lang),
        request_users=KeyboardButtonRequestUsers(request_id=1, user_is_bot=False),
    )
    cancel_btn = KeyboardButton(text=t("btn_cancel", lang))
    kb = ReplyKeyboardMarkup(
        keyboard=[[picker_btn], [cancel_btn]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await query.message.answer(
        t("set_tgid_prompt", lang, email=esc(email)),
        reply_markup=kb,
    )


@router.message(SetTgId.waiting, F.users_shared)
async def handle_tgid_pick(
    message: Message, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()

    users = message.users_shared.users if message.users_shared else []
    if not users:
        await message.answer(t("tgid_no_user", lang), reply_markup=ReplyKeyboardRemove())
        return

    tg_id = users[0].user_id
    await _apply_tgid(message, api, email, tg_id, lang)


@router.message(SetTgId.waiting, F.text)
async def handle_tgid_text(
    message: Message, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    data = await state.get_data()
    email = data["email"]
    text = (message.text or "").strip()

    cancel_texts = {t("btn_cancel", lc) for lc in ("en", "uz", "ru", "zh", "fa")} | {"/cancel"}
    if text in cancel_texts:
        await state.clear()
        await message.answer(t("cancelled", lang), reply_markup=ReplyKeyboardRemove())
        return

    try:
        tg_id = int(text)
    except ValueError:
        await message.answer(t("tgid_invalid", lang))
        return

    await state.clear()
    await _apply_tgid(message, api, email, tg_id, lang)


async def _apply_tgid(
    message: Message, api: XUIClient, email: str, tg_id: int, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    client = await api.get_client(email)
    if client is None:
        await message.answer(
            t("client_not_found", lang, email=esc(email)),
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    try:
        await api.update_client(email, client.to_update_payload(tgId=tg_id))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(
        t("tgid_done", lang, tg_id=tg_id, email=esc(email)),
        reply_markup=ReplyKeyboardRemove(),
    )
    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, lang, tz=tz, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated, lang),
        )


# --------------------------------------------------------------------------- #
# Extend days — quick-pick keyboard + text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "extend"))
async def cb_extend(query: CallbackQuery, callback_data: ClientCB, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.message.edit_text(
        t("extend_prompt", lang, email=esc(callback_data.email)),
        reply_markup=quick_days(callback_data.email, field="extend", lang=lang),
    )
    await query.answer()


@router.callback_query(QuickPickCB.filter(F.field == "extend"))
async def cb_qp_extend(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    email = callback_data.email
    if callback_data.value == -1:
        await state.set_state(ExtendClient.days)
        await state.update_data(email=email)
        await query.message.edit_text(
            t("extend_custom_prompt", lang, email=esc(email)),
            reply_markup=back_home(lang),
        )
        await query.answer()
        return

    days = callback_data.value
    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(
            t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang)
        )
        await query.answer()
        return

    try:
        await _apply_extend(api, client, days)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        await query.answer()
        return

    await query.answer("✅")
    await show_card(query, api, email, lang, tz)


@router.message(ExtendClient.days, F.text)
async def extend_days(message: Message, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer(t("extend_invalid", lang))
        await state.set_state(ExtendClient.days)
        await state.update_data(email=email)
        return

    client = await api.get_client(email)
    if client is None:
        await message.answer(t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang))
        return

    try:
        await _apply_extend(api, client, days)
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return

    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, lang, tz=tz, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated, lang),
        )
    else:
        await message.answer(back_home(lang))


async def _apply_extend(api: XUIClient, client: Client, days: int) -> None:
    if days == 0:
        await api.update_client(client.email, client.to_update_payload(expiryTime=0))
    elif client.expiry_time == 0:
        if days < 0:
            raise XUIError(
                f"{client.email} has no expiry — nothing to reduce. "
                "Send a positive number or use Set Expiry."
            )
        expiry_ms = int((time.time() + days * 86400) * 1000)
        await api.update_client(client.email, client.to_update_payload(expiryTime=expiry_ms))
    elif client.expiry_time < 0:
        new_expiry = client.expiry_time - days * 86400 * 1000
        await api.update_client(client.email, client.to_update_payload(expiryTime=new_expiry))
    else:
        result = await api.extend_client(client.email, add_days=days)
        if isinstance(result, dict) and result.get("skipped"):
            reasons = "; ".join(s.get("reason", "?") for s in result["skipped"])
            raise XUIError(f"Could not extend {client.email}: {reasons}")


# --------------------------------------------------------------------------- #
# Set quota — quick-pick keyboard + text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "set_quota"))
async def cb_set_quota(query: CallbackQuery, callback_data: ClientCB, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.message.edit_text(
        t("quota_prompt", lang, email=esc(callback_data.email)),
        reply_markup=quick_quota(callback_data.email, lang=lang),
    )
    await query.answer()


@router.callback_query(QuickPickCB.filter(F.field == "quota"))
async def cb_qp_quota(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    email = callback_data.email
    if callback_data.value == -1:
        await state.set_state(SetQuota.gb)
        await state.update_data(email=email)
        await query.message.edit_text(t("quota_custom_prompt", lang), reply_markup=back_home(lang))
        await query.answer()
        return

    gb = callback_data.value
    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang))
        await query.answer()
        return

    total_bytes = int(gb * (1024 ** 3))
    try:
        await api.update_client(email, client.to_update_payload(totalGB=total_bytes))
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        await query.answer()
        return

    await query.answer("✅")
    await show_card(query, api, email, lang, tz)


@router.message(SetQuota.gb, F.text)
async def set_quota_value(message: Message, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()
    try:
        gb = float(message.text.strip())
    except ValueError:
        await message.answer(t("quota_invalid", lang))
        await state.set_state(SetQuota.gb)
        await state.update_data(email=email)
        return
    client = await api.get_client(email)
    if client is None:
        await message.answer(t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang))
        return
    total_bytes = int(gb * (1024 ** 3))
    try:
        await api.update_client(email, client.to_update_payload(totalGB=total_bytes))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, lang, tz=tz, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated, lang),
        )
    else:
        await message.answer(t("updated_ok", lang), reply_markup=back_home(lang))


# --------------------------------------------------------------------------- #
# Set expiry — quick-pick keyboard + text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "set_expiry"))
async def cb_set_expiry(query: CallbackQuery, callback_data: ClientCB, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.message.edit_text(
        t("expiry_prompt", lang, email=esc(callback_data.email)),
        reply_markup=quick_days(callback_data.email, field="expiry", lang=lang),
    )
    await query.answer()


@router.callback_query(QuickPickCB.filter(F.field == "expiry"))
async def cb_qp_expiry(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    email = callback_data.email
    if callback_data.value == -1:
        await state.set_state(SetExpiry.days)
        await state.update_data(email=email)
        await query.message.edit_text(t("expiry_custom_prompt", lang), reply_markup=back_home(lang))
        await query.answer()
        return

    days = callback_data.value
    expiry_ms = 0 if days == 0 else int((time.time() + days * 86400) * 1000)

    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang))
        await query.answer()
        return

    try:
        await api.update_client(email, client.to_update_payload(expiryTime=expiry_ms))
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        await query.answer()
        return

    await query.answer("✅")
    await show_card(query, api, email, lang, tz)


@router.message(SetExpiry.days, F.text)
async def set_expiry_value(message: Message, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer(t("expiry_invalid", lang))
        await state.set_state(SetExpiry.days)
        await state.update_data(email=email)
        return
    client = await api.get_client(email)
    if client is None:
        await message.answer(t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang))
        return
    if days == 0:
        expiry_ms = 0
    elif days > 0:
        expiry_ms = int((time.time() + days * 86400) * 1000)
    else:
        expiry_ms = days * 86400 * 1000
    try:
        await api.update_client(email, client.to_update_payload(expiryTime=expiry_ms))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, lang, tz=tz, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated, lang),
        )
    else:
        await message.answer(t("updated_ok", lang), reply_markup=back_home(lang))


# --------------------------------------------------------------------------- #
# Set IP limit — quick-pick keyboard + text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "ip_limit"))
async def cb_ip_limit(query: CallbackQuery, callback_data: ClientCB, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.message.edit_text(
        t("iplimit_prompt", lang, email=esc(callback_data.email)),
        reply_markup=quick_iplimit(callback_data.email, lang=lang),
    )
    await query.answer()


@router.callback_query(QuickPickCB.filter(F.field == "iplimit"))
async def cb_qp_iplimit(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    email = callback_data.email
    if callback_data.value == -1:
        await state.set_state(SetIpLimit.count)
        await state.update_data(email=email)
        await query.message.edit_text(t("iplimit_custom_prompt", lang), reply_markup=back_home(lang))
        await query.answer()
        return

    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang))
        await query.answer()
        return

    try:
        await api.update_client(email, client.to_update_payload(limitIp=callback_data.value))
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        await query.answer()
        return

    await query.answer("✅")
    await show_card(query, api, email, lang, tz)


@router.message(SetIpLimit.count, F.text)
async def set_ip_limit_value(message: Message, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()
    try:
        count = int(message.text.strip())
        if count < 0:
            raise ValueError
    except ValueError:
        await message.answer(t("iplimit_invalid", lang))
        await state.set_state(SetIpLimit.count)
        await state.update_data(email=email)
        return
    client = await api.get_client(email)
    if client is None:
        await message.answer(t("client_not_found", lang, email=esc(email)), reply_markup=back_home(lang))
        return
    try:
        await api.update_client(email, client.to_update_payload(limitIp=count))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, lang, tz=tz, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated, lang),
        )
    else:
        await message.answer(t("updated_ok", lang), reply_markup=back_home(lang))


# --------------------------------------------------------------------------- #
# Create client wizard
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "create"))
async def cb_create(
    query: CallbackQuery, state: FSMContext, api: XUIClient, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    await query.answer(t("loading_inbounds", lang))
    try:
        options = await api.inbound_options()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    if not options:
        await query.message.edit_text(t("create_no_inbounds", lang), reply_markup=back_home(lang))
        return

    valid_ids = {o.id for o in options}
    opts_map = {o.id: (o.remark, o.protocol, o.port) for o in options}

    defaults = [i for i in settings.default_inbound_ids if i in valid_ids]
    if defaults:
        await state.update_data(selected=defaults, opts=opts_map)
        await state.set_state(CreateClient.email)
        await query.message.edit_text(
            t("create_email_prompt_default", lang),
            reply_markup=back_home(lang),
        )
        return

    await state.set_state(CreateClient.inbounds)
    await state.update_data(selected=[], opts=opts_map)
    await query.message.edit_text(
        t("create_inbounds_prompt", lang),
        reply_markup=inbound_picker(options, set(), lang),
    )


def _opts_from_state(data: dict) -> list:
    from bot.api.models import InboundOption

    opts = data.get("opts", {})
    out = []
    for oid, (remark, proto, port) in opts.items():
        out.append(InboundOption(id=int(oid), remark=remark, protocol=proto, port=port))
    return sorted(out, key=lambda o: o.id)


@router.callback_query(CreateClient.inbounds, InbPickCB.filter(F.action == "toggle"))
async def create_toggle_inbound(
    query: CallbackQuery, callback_data: InbPickCB, state: FSMContext, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    data = await state.get_data()
    selected = set(data.get("selected", []))
    if callback_data.inbound_id in selected:
        selected.discard(callback_data.inbound_id)
    else:
        selected.add(callback_data.inbound_id)
    await state.update_data(selected=list(selected))
    await query.message.edit_reply_markup(
        reply_markup=inbound_picker(_opts_from_state(data), selected, lang)
    )
    await query.answer()


@router.callback_query(CreateClient.inbounds, InbPickCB.filter(F.action == "done"))
async def create_inbounds_done(query: CallbackQuery, state: FSMContext, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    data = await state.get_data()
    if not data.get("selected"):
        await query.answer(t("create_pick_at_least_one", lang), show_alert=True)
        return
    await state.set_state(CreateClient.email)
    await query.message.edit_text(t("create_email_prompt", lang), reply_markup=back_home(lang))
    await query.answer()


@router.message(CreateClient.email, F.text)
async def create_email(message: Message, state: FSMContext, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    email = message.text.strip()
    if " " in email or not email:
        await message.answer(t("create_email_invalid", lang))
        return
    await state.update_data(email=email)
    await state.set_state(CreateClient.quota)
    await message.answer(
        t("quota_prompt", lang, email=esc(email)),
        reply_markup=quick_quota(lang=lang),
    )


@router.callback_query(CreateClient.quota, QuickPickCB.filter(F.field == "wiz_quota"))
async def cb_wiz_quota(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    if callback_data.value == -1:
        await query.message.edit_text(
            t("quota_custom_prompt_wizard", lang, default=settings.default_quota_gb),
            reply_markup=back_home(lang),
        )
        await query.answer()
        return
    await state.update_data(quota=float(callback_data.value))
    await state.set_state(CreateClient.days)
    await query.message.edit_text(
        t("create_validity_prompt", lang),
        reply_markup=quick_days(field="wiz_days", lang=lang),
    )
    await query.answer()


@router.message(CreateClient.quota, F.text)
async def create_quota(message: Message, state: FSMContext, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    raw = message.text.strip()
    try:
        quota = float(raw) if raw else settings.default_quota_gb
    except ValueError:
        await message.answer(t("quota_invalid", lang))
        return
    await state.update_data(quota=quota)
    await state.set_state(CreateClient.days)
    await message.answer(
        t("create_validity_prompt", lang),
        reply_markup=quick_days(field="wiz_days", lang=lang),
    )


@router.callback_query(CreateClient.days, QuickPickCB.filter(F.field == "wiz_days"))
async def cb_wiz_days(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None
) -> None:
    if callback_data.value == -1:
        await query.message.edit_text(
            t("days_custom_prompt_wizard", lang, default=settings.default_days),
            reply_markup=back_home(lang),
        )
        await query.answer()
        return
    await _finish_wizard(query, state, callback_data.value, lang, tz)
    await query.answer()


@router.message(CreateClient.days, F.text)
async def create_days(message: Message, state: FSMContext, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    raw = message.text.strip()
    try:
        days = int(raw) if raw else settings.default_days
    except ValueError:
        await message.answer(t("expiry_invalid", lang))
        return
    data = await state.get_data()
    await state.update_data(days=days)
    await state.set_state(CreateClient.confirm)
    quota_label = "∞" if not data["quota"] else f"{data['quota']:g} GB"
    days_label = "∞" if not days else f"{days} days"
    inbounds = ", ".join(f"#{i}" for i in data["selected"])
    await message.answer(
        t("create_confirm", lang, email=esc(data["email"]), quota=quota_label, days=days_label, inbounds=inbounds),
        reply_markup=confirm_create(lang),
    )


async def _finish_wizard(query: CallbackQuery, state: FSMContext, days: int, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    data = await state.get_data()
    await state.update_data(days=days)
    await state.set_state(CreateClient.confirm)
    quota = data.get("quota", 0)
    quota_label = "∞" if not quota else f"{quota:g} GB"
    days_label = "∞" if not days else f"{days} days"
    inbounds = ", ".join(f"#{i}" for i in data["selected"])
    await query.message.edit_text(
        t("create_confirm", lang, email=esc(data["email"]), quota=quota_label, days=days_label, inbounds=inbounds),
        reply_markup=confirm_create(lang),
    )


@router.callback_query(
    CreateClient.confirm, ConfirmCB.filter((F.action == "yes") & (F.scope == "create"))
)
async def create_confirm(query: CallbackQuery, state: FSMContext, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    data = await state.get_data()
    await state.clear()
    builder = ClientCreate(
        email=data["email"],
        quota_gb=data["quota"],
        days=data["days"],
    )
    try:
        await api.add_client(builder.to_payload(), [int(i) for i in data["selected"]])
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        await query.answer()
        return
    await query.answer(t("created_ok", lang))
    client = await api.get_client(data["email"])
    if client:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, client, tz)
        await query.message.edit_text(
            render_client(client, lang, tz=tz, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(client, lang),
        )
    else:
        await query.message.edit_text(
            t("create_done", lang, email=esc(data["email"])), reply_markup=back_home(lang)
        )
