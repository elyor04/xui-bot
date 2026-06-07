"""Admin client management: list, view, create, extend, delete, reset, links, QR, quota."""
from __future__ import annotations

import math
import time
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
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
from bot.keyboards.admin import (
    back_home,
    client_card,
    clients_list,
    confirm_create,
    confirm_delete,
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
    LOCAL_TZ,
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
    *,
    inbound_remarks: list[str] | None = None,
    is_online: bool | None = None,
    last_online_str: str | None = None,
) -> str:
    inbounds_label = (
        ", ".join(inbound_remarks) if inbound_remarks
        else ", ".join(f"#{i}" for i in c.inbound_ids) or "—"
    )
    enabled_mark = "✅ Yes" if c.enable else "❌ No"
    now_ms = int(time.time() * 1000)
    is_active = c.enable and (c.expiry_time == 0 or c.expiry_time > now_ms)
    active_mark = "✅ Yes" if is_active else "❌ No"
    quota_label = fmt_quota_card(c.total_gb, c.reset)
    expiry_label = fmt_expiry_card(c.expiry_time, c.reset)
    refresh_ts = datetime.now(tz=LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"📧 Email: {esc(c.email)}",
        f"🔗 Inbounds: {inbounds_label}",
        f"🚨 Enabled: {enabled_mark}",
    ]
    if is_online is not None:
        conn = "🟢 Online" if is_online else "🔴 Offline"
        lines.append(f"🌐 Connection status: {conn}")
    if last_online_str:
        lines.append(f"🔙 Last online: {last_online_str}")
    lines += [
        f"💡 Active: {active_mark}",
        f"📅 Expire Date: {expiry_label}",
        f"🔼 Upload: ↑{compact_bytes(c.up)}",
        f"🔽 Download: ↓{compact_bytes(c.down)}",
        f"📊 Total: ↑↓{compact_bytes(c.up + c.down)} / {quota_label}",
        "",
        f"📋🔄 Refreshed On: {refresh_ts}",
    ]
    return "\n".join(lines)


async def _fetch_render_extras(
    api: XUIClient, client: Client
) -> tuple[list[str] | None, bool | None, str | None]:
    """Return (inbound_remarks, is_online, last_online_str) for a client card."""
    inbound_remarks: list[str] | None = None
    is_online: bool | None = None
    last_online_str: str | None = None

    # Use the lightweight options endpoint (no settings/client data) for remark lookup.
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

    # Prefer lastOnline from the client model (already fetched from /clients/traffic/:email).
    # Fall back to parsing the IP log only when lastOnline is not available.
    if client.last_online > 0:
        try:
            dt = datetime.fromtimestamp(client.last_online / 1000, tz=LOCAL_TZ)
            last_online_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            pass

    if not last_online_str:
        try:
            raw_ips = await api.client_ips(client.email)
            last_online_str = extract_last_online(raw_ips)
        except Exception:
            pass

    return inbound_remarks, is_online, last_online_str


async def show_card(query: CallbackQuery, api: XUIClient, email: str) -> None:
    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        return
    inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, client)
    await query.message.edit_text(
        render_client(client, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
        reply_markup=client_card(client),
    )


# --------------------------------------------------------------------------- #
# List + view
# --------------------------------------------------------------------------- #
async def _render_page(
    api: XUIClient, page: int, inbound_id: int = -1
) -> tuple[str, list[Client], int]:
    all_clients = sorted(await api.list_clients(), key=lambda c: c.id)
    if inbound_id != -1:
        clients = [c for c in all_clients if inbound_id in c.inbound_ids]
        filter_label = f" · inbound #{inbound_id}"
    else:
        clients = all_clients
        filter_label = ""
    pages = max(1, math.ceil(len(clients) / PAGE_SIZE))
    page = max(0, min(page, pages - 1))
    chunk = clients[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    text = f"👥 <b>Clients</b>{filter_label} — {len(clients)} total"
    return text, chunk, pages


@router.callback_query(MenuCB.filter(F.action == "clients"))
async def cb_clients(query: CallbackQuery, api: XUIClient) -> None:
    await query.answer("Loading…")
    try:
        options = await api.inbound_options()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    await query.message.edit_text(
        "👥 <b>Clients</b> — pick an inbound to filter, or view all:",
        reply_markup=inbound_filter(options),
    )


@router.callback_query(PageCB.filter(F.target == "clients"))
async def cb_clients_page(query: CallbackQuery, callback_data: PageCB, api: XUIClient) -> None:
    await query.answer()
    try:
        text, chunk, pages = await _render_page(api, callback_data.page, callback_data.inbound_id)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    await query.message.edit_text(
        text,
        reply_markup=clients_list(chunk, callback_data.page, pages, callback_data.inbound_id),
    )


@router.callback_query(ClientCB.filter(F.action == "view"))
async def cb_view(query: CallbackQuery, callback_data: ClientCB, api: XUIClient) -> None:
    await query.answer()
    await show_card(query, api, callback_data.email)


@router.callback_query(ClientCB.filter(F.action == "refresh"))
async def cb_refresh(query: CallbackQuery, callback_data: ClientCB, api: XUIClient) -> None:
    await query.answer("Refreshing…")
    await show_card(query, api, callback_data.email)


# --------------------------------------------------------------------------- #
# Find by email
# --------------------------------------------------------------------------- #
def _pick_list_kb(items: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        email = item.get("email", "")
        builder.button(text=email, callback_data=ClientCB(action="view", email=email))
    builder.adjust(1)
    return builder.as_markup()


async def _search_and_show(message: Message, api: XUIClient, search: str) -> None:
    """Search by substring and open card (1 match) or show a pick list (2-25 matches)."""
    try:
        result = await api.search_clients(search, page_size=25)
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return

    items: list[dict] = result.get("items") or []
    filtered: int = result.get("filtered", len(items))

    if filtered == 0:
        await message.answer(
            f"No clients matching <code>{esc(search)}</code>.", reply_markup=back_home()
        )
        return

    if filtered > 25:
        await message.answer(
            f"🔎 <b>{filtered} matches</b> for <code>{esc(search)}</code> — refine your search."
        )
        return

    if filtered == 1:
        client = await api.get_client(items[0]["email"])
        if client is None:
            await message.answer(
                f"Client <code>{esc(items[0]['email'])}</code> not found.", reply_markup=back_home()
            )
            return
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, client)
        await message.answer(
            render_client(client, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(client),
        )
        return

    await message.answer(
        f"🔎 <b>{filtered} matches</b> for <code>{esc(search)}</code>:",
        reply_markup=_pick_list_kb(items),
    )


@router.callback_query(MenuCB.filter(F.action == "find"))
async def cb_find(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(FindClient.email)
    await query.message.edit_text(
        "🔎 Send an email (or partial email) to search.", reply_markup=back_home()
    )
    await query.answer()


@router.message(Command("find"))
async def cmd_find(message: Message, command: CommandObject, api: XUIClient) -> None:
    search = (command.args or "").strip()
    if not search:
        await message.answer("Usage: <code>/find &lt;email&gt;</code>")
        return
    await _search_and_show(message, api, search)


@router.message(FindClient.email, F.text)
async def find_email(message: Message, state: FSMContext, api: XUIClient) -> None:
    await state.clear()
    await _search_and_show(message, api, message.text.strip())


# --------------------------------------------------------------------------- #
# Per-client actions: reset, toggle, links, IPs, sub, QR
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "reset"))
async def cb_reset(query: CallbackQuery, callback_data: ClientCB, api: XUIClient) -> None:
    try:
        await api.reset_client_traffic(callback_data.email)
        await query.answer("Traffic reset ✅")
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
    await show_card(query, api, callback_data.email)


@router.callback_query(ClientCB.filter(F.action == "toggle"))
async def cb_toggle(query: CallbackQuery, callback_data: ClientCB, api: XUIClient) -> None:
    client = await api.get_client(callback_data.email)
    if client is None:
        await query.answer("Not found", show_alert=True)
        return
    payload = client.to_update_payload(enable=not client.enable)
    try:
        await api.update_client(client.email, payload)
        await query.answer("Updated ✅")
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
    await show_card(query, api, callback_data.email)


@router.callback_query(ClientCB.filter(F.action == "links"))
async def cb_links(query: CallbackQuery, callback_data: ClientCB, api: XUIClient) -> None:
    await query.answer("Loading…")
    try:
        links = await api.client_links(callback_data.email)
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
        return
    if not links:
        body = "No URL-style configs for this client (protocol may not support links)."
    else:
        body = "\n\n".join(f"<code>{esc(u)}</code>" for u in links)
    await query.message.edit_text(
        f"🔗 <b>{esc(callback_data.email)}</b>\n\n{body}", reply_markup=back_home()
    )


@router.callback_query(ClientCB.filter(F.action == "ips"))
async def cb_ips(query: CallbackQuery, callback_data: ClientCB, api: XUIClient) -> None:
    await query.answer("Loading…")
    try:
        raw = await api.client_ips(callback_data.email)
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
        return
    body = fmt_ips(raw)
    await query.message.edit_text(
        f"🌐 <b>{esc(callback_data.email)}</b>\n\n{body}",
        reply_markup=ip_log_kb(callback_data.email),
    )


@router.callback_query(ClientCB.filter(F.action == "clearips"))
async def cb_clearips(query: CallbackQuery, callback_data: ClientCB, api: XUIClient) -> None:
    try:
        await api.clear_client_ips(callback_data.email)
        await query.answer("IP list cleared ✅")
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)
    await show_card(query, api, callback_data.email)


@router.callback_query(ClientCB.filter(F.action == "sublinks"))
async def cb_sublinks(
    query: CallbackQuery, callback_data: ClientCB, api: XUIClient, settings: Settings
) -> None:
    await query.answer("Loading…")
    client = await api.get_client(callback_data.email)
    if client is None:
        await query.message.edit_text(
            f"Client <code>{esc(callback_data.email)}</code> not found.",
            reply_markup=back_home(),
        )
        return

    parts: list[str] = []
    if client.sub_id and settings.sub_base_url:
        sub_url = settings.sub_base_url.rstrip("/") + "/" + client.sub_id
        parts.append(f"<b>Subscription URL</b>\n<code>{esc(sub_url)}</code>")
    else:
        parts.append(
            "⚠️ No subscription URL available.\n"
            "Set <code>SUB_BASE_URL</code> in your bot config to enable this."
        )

    await query.message.edit_text(
        f"🔗 <b>Sub links · {esc(callback_data.email)}</b>\n\n" + "\n\n".join(parts),
        reply_markup=back_home(),
    )


@router.callback_query(ClientCB.filter(F.action == "qr"))
async def cb_qr(
    query: CallbackQuery, callback_data: ClientCB, api: XUIClient, settings: Settings
) -> None:
    await query.answer("Generating QR…")
    client = await api.get_client(callback_data.email)
    if client is None:
        await query.message.edit_text(
            f"Client <code>{esc(callback_data.email)}</code> not found.",
            reply_markup=back_home(),
        )
        return

    sent_any = False

    if client.sub_id and settings.sub_base_url:
        sub_url = settings.sub_base_url.rstrip("/") + "/" + client.sub_id
        png = make_qr_png(sub_url)
        file = BufferedInputFile(png, filename=f"{callback_data.email}_sub.png")
        await query.message.answer_document(
            file, caption=f"📷 Sub URL QR · <code>{esc(callback_data.email)}</code>"
        )
        sent_any = True

    try:
        links = await api.client_links(callback_data.email)
        for i, link in enumerate(links[:5], 1):
            png = make_qr_png(link)
            file = BufferedInputFile(png, filename=f"{callback_data.email}_link{i}.png")
            await query.message.answer_document(
                file, caption=f"📷 Config #{i} · <code>{esc(callback_data.email)}</code>"
            )
            sent_any = True
    except XUIError:
        pass

    if not sent_any:
        await query.message.edit_text(
            "No QR data available (no sub URL or links for this client).",
            reply_markup=back_home(),
        )
    else:
        await query.message.answer("✅ Done.", reply_markup=back_home())


# --------------------------------------------------------------------------- #
# Delete (with confirmation)
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "del"))
async def cb_del(query: CallbackQuery, callback_data: ClientCB) -> None:
    await query.message.edit_text(
        f"🗑 Delete <code>{esc(callback_data.email)}</code>? This cannot be undone.",
        reply_markup=confirm_delete(callback_data.email),
    )
    await query.answer()


@router.callback_query(ConfirmCB.filter((F.action == "yes") & (F.scope == "del")))
async def cb_del_confirm(query: CallbackQuery, callback_data: ConfirmCB, api: XUIClient) -> None:
    try:
        await api.delete_client(callback_data.arg)
        await query.answer("Deleted ✅")
        await query.message.edit_text(
            f"🗑 Deleted <code>{esc(callback_data.arg)}</code>.", reply_markup=back_home()
        )
    except XUIError as exc:
        await query.answer(str(exc)[:180], show_alert=True)


# --------------------------------------------------------------------------- #
# Set TG ID — native Telegram user picker + numeric text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "set_tgid"))
async def cb_set_tgid(
    query: CallbackQuery, callback_data: ClientCB, state: FSMContext
) -> None:
    email = callback_data.email
    await state.set_state(SetTgId.waiting)
    await state.update_data(email=email)
    await query.answer()

    picker_btn = KeyboardButton(
        text="👤 Pick a Telegram user",
        request_users=KeyboardButtonRequestUsers(request_id=1, user_is_bot=False),
    )
    cancel_btn = KeyboardButton(text="✖️ Cancel")
    kb = ReplyKeyboardMarkup(
        keyboard=[[picker_btn], [cancel_btn]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await query.message.answer(
        f"👤 Assign a Telegram user to <code>{esc(email)}</code>.\n\n"
        "Tap <b>Pick a Telegram user</b> to choose from your contacts, "
        "or type a numeric Telegram ID directly.",
        reply_markup=kb,
    )


@router.message(SetTgId.waiting, F.users_shared)
async def handle_tgid_pick(
    message: Message, state: FSMContext, api: XUIClient
) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()

    users = message.users_shared.users if message.users_shared else []
    if not users:
        await message.answer("No user selected.", reply_markup=ReplyKeyboardRemove())
        return

    tg_id = users[0].user_id
    await _apply_tgid(message, api, email, tg_id)


@router.message(SetTgId.waiting, F.text)
async def handle_tgid_text(
    message: Message, state: FSMContext, api: XUIClient
) -> None:
    data = await state.get_data()
    email = data["email"]
    text = (message.text or "").strip()

    if text in ("✖️ Cancel", "/cancel"):
        await state.clear()
        await message.answer("Cancelled.", reply_markup=ReplyKeyboardRemove())
        return

    try:
        tg_id = int(text)
    except ValueError:
        await message.answer(
            "Please send a <b>numeric</b> Telegram user ID, or use the picker button."
        )
        return

    await state.clear()
    await _apply_tgid(message, api, email, tg_id)


async def _apply_tgid(
    message: Message, api: XUIClient, email: str, tg_id: int
) -> None:
    client = await api.get_client(email)
    if client is None:
        await message.answer(
            f"Client <code>{esc(email)}</code> not found.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return
    try:
        await api.update_client(email, client.to_update_payload(tgId=tg_id))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(
        f"✅ TG ID <code>{tg_id}</code> assigned to <code>{esc(email)}</code>.",
        reply_markup=ReplyKeyboardRemove(),
    )
    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated),
        )


# --------------------------------------------------------------------------- #
# Extend days — quick-pick keyboard + text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "extend"))
async def cb_extend(query: CallbackQuery, callback_data: ClientCB) -> None:
    await query.message.edit_text(
        f"➕ <b>Extend</b> <code>{esc(callback_data.email)}</code> — pick days to add:",
        reply_markup=quick_days(callback_data.email, field="extend"),
    )
    await query.answer()


@router.callback_query(QuickPickCB.filter(F.field == "extend"))
async def cb_qp_extend(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, api: XUIClient
) -> None:
    email = callback_data.email
    if callback_data.value == -1:  # Custom → fall back to text FSM
        await state.set_state(ExtendClient.days)
        await state.update_data(email=email)
        await query.message.edit_text(
            f"➕ How many days to add to <code>{esc(email)}</code>?\n"
            "Send a number (negative to reduce).",
            reply_markup=back_home(),
        )
        await query.answer()
        return

    days = callback_data.value  # 0 = remove expiry
    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        await query.answer()
        return

    try:
        await _apply_extend(api, client, days)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        await query.answer()
        return

    await query.answer("✅")
    await show_card(query, api, email)


@router.message(ExtendClient.days, F.text)
async def extend_days(message: Message, state: FSMContext, api: XUIClient) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer("Please send a whole number, e.g. <code>30</code>.")
        await state.set_state(ExtendClient.days)
        await state.update_data(email=email)
        return

    client = await api.get_client(email)
    if client is None:
        await message.answer(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        return

    try:
        await _apply_extend(api, client, days)
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return

    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated),
        )
    else:
        await message.answer(f"Extended by {days} days.", reply_markup=back_home())


async def _apply_extend(api: XUIClient, client: Client, days: int) -> None:
    """Core extend logic covering all three expiry modes."""
    if days == 0:
        # Remove expiry (make unlimited)
        await api.update_client(client.email, client.to_update_payload(expiryTime=0))
    elif client.expiry_time == 0:
        # Unlimited client — BulkAdjust refuses; set absolute timestamp from now.
        if days < 0:
            raise XUIError(
                f"{client.email} has no expiry — nothing to reduce. "
                "Send a positive number or use Set Expiry."
            )
        expiry_ms = int((time.time() + days * 86400) * 1000)
        await api.update_client(client.email, client.to_update_payload(expiryTime=expiry_ms))
    elif client.expiry_time < 0:
        # Relative (days-from-first-use) mode: extend by making the value more negative.
        new_expiry = client.expiry_time - days * 86400 * 1000
        await api.update_client(client.email, client.to_update_payload(expiryTime=new_expiry))
    else:
        # Absolute timestamp — use BulkAdjust; check for skipped.
        result = await api.extend_client(client.email, add_days=days)
        if isinstance(result, dict) and result.get("skipped"):
            reasons = "; ".join(s.get("reason", "?") for s in result["skipped"])
            raise XUIError(f"Could not extend {client.email}: {reasons}")


# --------------------------------------------------------------------------- #
# Set quota — quick-pick keyboard + text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "set_quota"))
async def cb_set_quota(query: CallbackQuery, callback_data: ClientCB) -> None:
    await query.message.edit_text(
        f"💽 Traffic quota for <code>{esc(callback_data.email)}</code>:",
        reply_markup=quick_quota(callback_data.email),
    )
    await query.answer()


@router.callback_query(QuickPickCB.filter(F.field == "quota"))
async def cb_qp_quota(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, api: XUIClient
) -> None:
    email = callback_data.email
    if callback_data.value == -1:
        await state.set_state(SetQuota.gb)
        await state.update_data(email=email)
        await query.message.edit_text(
            "💽 Send quota in <b>GB</b> (0 = unlimited):", reply_markup=back_home()
        )
        await query.answer()
        return

    gb = callback_data.value
    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        await query.answer()
        return

    total_bytes = int(gb * (1024 ** 3))
    try:
        await api.update_client(email, client.to_update_payload(totalGB=total_bytes))
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        await query.answer()
        return

    await query.answer("✅")
    await show_card(query, api, email)


@router.message(SetQuota.gb, F.text)
async def set_quota_value(message: Message, state: FSMContext, api: XUIClient) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()
    try:
        gb = float(message.text.strip())
    except ValueError:
        await message.answer("Send a number, e.g. <code>50</code> (or 0 for unlimited).")
        await state.set_state(SetQuota.gb)
        await state.update_data(email=email)
        return
    client = await api.get_client(email)
    if client is None:
        await message.answer(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        return
    total_bytes = int(gb * (1024 ** 3))
    try:
        await api.update_client(email, client.to_update_payload(totalGB=total_bytes))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated),
        )
    else:
        await message.answer(f"Quota updated to {gb:g} GB.", reply_markup=back_home())


# --------------------------------------------------------------------------- #
# Set expiry — quick-pick keyboard + text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "set_expiry"))
async def cb_set_expiry(query: CallbackQuery, callback_data: ClientCB) -> None:
    await query.message.edit_text(
        f"📅 Expiry for <code>{esc(callback_data.email)}</code> — pick days from today:",
        reply_markup=quick_days(callback_data.email, field="expiry"),
    )
    await query.answer()


@router.callback_query(QuickPickCB.filter(F.field == "expiry"))
async def cb_qp_expiry(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, api: XUIClient
) -> None:
    email = callback_data.email
    if callback_data.value == -1:
        await state.set_state(SetExpiry.days)
        await state.update_data(email=email)
        await query.message.edit_text(
            "📅 Send number of <b>days from now</b> (0 = no expiry, negative = days from first use):",
            reply_markup=back_home(),
        )
        await query.answer()
        return

    days = callback_data.value
    if days == 0:
        expiry_ms = 0
    else:
        expiry_ms = int((time.time() + days * 86400) * 1000)

    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        await query.answer()
        return

    try:
        await api.update_client(email, client.to_update_payload(expiryTime=expiry_ms))
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        await query.answer()
        return

    await query.answer("✅")
    await show_card(query, api, email)


@router.message(SetExpiry.days, F.text)
async def set_expiry_value(message: Message, state: FSMContext, api: XUIClient) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer("Send a whole number, e.g. <code>30</code>.")
        await state.set_state(SetExpiry.days)
        await state.update_data(email=email)
        return
    client = await api.get_client(email)
    if client is None:
        await message.answer(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        return
    if days == 0:
        expiry_ms = 0
    elif days > 0:
        expiry_ms = int((time.time() + days * 86400) * 1000)
    else:
        expiry_ms = days * 86400 * 1000  # negative = days-from-first-use
    try:
        await api.update_client(email, client.to_update_payload(expiryTime=expiry_ms))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated),
        )
    else:
        await message.answer("Expiry updated.", reply_markup=back_home())


# --------------------------------------------------------------------------- #
# Set IP limit — quick-pick keyboard + text fallback
# --------------------------------------------------------------------------- #
@router.callback_query(ClientCB.filter(F.action == "ip_limit"))
async def cb_ip_limit(query: CallbackQuery, callback_data: ClientCB) -> None:
    await query.message.edit_text(
        f"🔢 IP limit for <code>{esc(callback_data.email)}</code>:",
        reply_markup=quick_iplimit(callback_data.email),
    )
    await query.answer()


@router.callback_query(QuickPickCB.filter(F.field == "iplimit"))
async def cb_qp_iplimit(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, api: XUIClient
) -> None:
    email = callback_data.email
    if callback_data.value == -1:
        await state.set_state(SetIpLimit.count)
        await state.update_data(email=email)
        await query.message.edit_text(
            "🔢 Send max simultaneous IPs (0 = unlimited):", reply_markup=back_home()
        )
        await query.answer()
        return

    client = await api.get_client(email)
    if client is None:
        await query.message.edit_text(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        await query.answer()
        return

    try:
        await api.update_client(email, client.to_update_payload(limitIp=callback_data.value))
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        await query.answer()
        return

    await query.answer("✅")
    await show_card(query, api, email)


@router.message(SetIpLimit.count, F.text)
async def set_ip_limit_value(message: Message, state: FSMContext, api: XUIClient) -> None:
    data = await state.get_data()
    email = data["email"]
    await state.clear()
    try:
        count = int(message.text.strip())
        if count < 0:
            raise ValueError
    except ValueError:
        await message.answer("Send a non-negative whole number, e.g. <code>3</code>.")
        await state.set_state(SetIpLimit.count)
        await state.update_data(email=email)
        return
    client = await api.get_client(email)
    if client is None:
        await message.answer(
            f"Client <code>{esc(email)}</code> not found.", reply_markup=back_home()
        )
        return
    try:
        await api.update_client(email, client.to_update_payload(limitIp=count))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    updated = await api.get_client(email)
    if updated:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, updated)
        await message.answer(
            render_client(updated, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(updated),
        )
    else:
        await message.answer(f"IP limit set to {count or '∞'}.", reply_markup=back_home())


# --------------------------------------------------------------------------- #
# Create client wizard
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "create"))
async def cb_create(
    query: CallbackQuery, state: FSMContext, api: XUIClient, settings: Settings
) -> None:
    await query.answer("Loading inbounds…")
    try:
        options = await api.inbound_options()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    if not options:
        await query.message.edit_text("No inbounds available.", reply_markup=back_home())
        return

    valid_ids = {o.id for o in options}
    opts_map = {o.id: (o.remark, o.protocol, o.port) for o in options}

    defaults = [i for i in settings.default_inbound_ids if i in valid_ids]
    if defaults:
        await state.update_data(selected=defaults, opts=opts_map)
        await state.set_state(CreateClient.email)
        await query.message.edit_text(
            "➕ <b>New client</b>\nSend the <b>email</b> (label) for the new client.",
            reply_markup=back_home(),
        )
        return

    await state.set_state(CreateClient.inbounds)
    await state.update_data(selected=[], opts=opts_map)
    await query.message.edit_text(
        "➕ <b>New client</b>\nSelect one or more inbounds, then Continue.",
        reply_markup=inbound_picker(options, set()),
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
    query: CallbackQuery, callback_data: InbPickCB, state: FSMContext
) -> None:
    data = await state.get_data()
    selected = set(data.get("selected", []))
    if callback_data.inbound_id in selected:
        selected.discard(callback_data.inbound_id)
    else:
        selected.add(callback_data.inbound_id)
    await state.update_data(selected=list(selected))
    await query.message.edit_reply_markup(
        reply_markup=inbound_picker(_opts_from_state(data), selected)
    )
    await query.answer()


@router.callback_query(CreateClient.inbounds, InbPickCB.filter(F.action == "done"))
async def create_inbounds_done(query: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("selected"):
        await query.answer("Pick at least one inbound.", show_alert=True)
        return
    await state.set_state(CreateClient.email)
    await query.message.edit_text(
        "✏️ Send the <b>email</b> (label) for the new client.", reply_markup=back_home()
    )
    await query.answer()


@router.message(CreateClient.email, F.text)
async def create_email(message: Message, state: FSMContext) -> None:
    email = message.text.strip()
    if " " in email or not email:
        await message.answer("Email must be a single token without spaces. Try again.")
        return
    await state.update_data(email=email)
    await state.set_state(CreateClient.quota)
    await message.answer(
        f"💽 Traffic quota for <code>{esc(email)}</code>:",
        reply_markup=quick_quota(),
    )


@router.callback_query(CreateClient.quota, QuickPickCB.filter(F.field == "wiz_quota"))
async def cb_wiz_quota(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, settings: Settings
) -> None:
    if callback_data.value == -1:
        await query.message.edit_text(
            f"💽 Send quota in <b>GB</b> (0 = unlimited).\nDefault: <code>{settings.default_quota_gb}</code>",
            reply_markup=back_home(),
        )
        await query.answer()
        return
    await state.update_data(quota=float(callback_data.value))
    await state.set_state(CreateClient.days)
    await query.message.edit_text(
        "📅 Validity — pick days from today:",
        reply_markup=quick_days(field="wiz_days"),
    )
    await query.answer()


@router.message(CreateClient.quota, F.text)
async def create_quota(message: Message, state: FSMContext, settings: Settings) -> None:
    raw = message.text.strip()
    try:
        quota = float(raw) if raw else settings.default_quota_gb
    except ValueError:
        await message.answer("Send a number, e.g. <code>50</code> (or 0 for unlimited).")
        return
    await state.update_data(quota=quota)
    await state.set_state(CreateClient.days)
    await message.answer(
        "📅 Validity — pick days from today:",
        reply_markup=quick_days(field="wiz_days"),
    )


@router.callback_query(CreateClient.days, QuickPickCB.filter(F.field == "wiz_days"))
async def cb_wiz_days(
    query: CallbackQuery, callback_data: QuickPickCB, state: FSMContext, settings: Settings
) -> None:
    if callback_data.value == -1:
        await query.message.edit_text(
            f"📅 Send validity in <b>days</b> (0 = unlimited).\nDefault: <code>{settings.default_days}</code>",
            reply_markup=back_home(),
        )
        await query.answer()
        return
    await _finish_wizard(query, state, callback_data.value)
    await query.answer()


@router.message(CreateClient.days, F.text)
async def create_days(message: Message, state: FSMContext, settings: Settings) -> None:
    raw = message.text.strip()
    try:
        days = int(raw) if raw else settings.default_days
    except ValueError:
        await message.answer("Send a whole number, e.g. <code>30</code> (or 0 for unlimited).")
        return
    data = await state.get_data()
    await state.update_data(days=days)
    await state.set_state(CreateClient.confirm)
    quota_label = "∞" if not data["quota"] else f"{data['quota']:g} GB"
    days_label = "∞" if not days else f"{days} days"
    inbounds = ", ".join(f"#{i}" for i in data["selected"])
    await message.answer(
        "🧾 <b>Confirm new client</b>\n\n"
        f"Email: <code>{esc(data['email'])}</code>\n"
        f"Quota: <b>{quota_label}</b>\n"
        f"Validity: <b>{days_label}</b>\n"
        f"Inbounds: {inbounds}",
        reply_markup=confirm_create(),
    )


async def _finish_wizard(query: CallbackQuery, state: FSMContext, days: int) -> None:
    data = await state.get_data()
    await state.update_data(days=days)
    await state.set_state(CreateClient.confirm)
    quota = data.get("quota", 0)
    quota_label = "∞" if not quota else f"{quota:g} GB"
    days_label = "∞" if not days else f"{days} days"
    inbounds = ", ".join(f"#{i}" for i in data["selected"])
    await query.message.edit_text(
        "🧾 <b>Confirm new client</b>\n\n"
        f"Email: <code>{esc(data['email'])}</code>\n"
        f"Quota: <b>{quota_label}</b>\n"
        f"Validity: <b>{days_label}</b>\n"
        f"Inbounds: {inbounds}",
        reply_markup=confirm_create(),
    )


@router.callback_query(
    CreateClient.confirm, ConfirmCB.filter((F.action == "yes") & (F.scope == "create"))
)
async def create_confirm(query: CallbackQuery, state: FSMContext, api: XUIClient) -> None:
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
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        await query.answer()
        return
    await query.answer("Created ✅")
    client = await api.get_client(data["email"])
    if client:
        inbound_remarks, is_online, last_online_str = await _fetch_render_extras(api, client)
        await query.message.edit_text(
            render_client(client, inbound_remarks=inbound_remarks, is_online=is_online, last_online_str=last_online_str),
            reply_markup=client_card(client),
        )
    else:
        await query.message.edit_text(
            f"✅ Created <code>{esc(data['email'])}</code>.", reply_markup=back_home()
        )
