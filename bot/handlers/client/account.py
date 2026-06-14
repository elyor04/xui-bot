"""Client (end-user) side: link to a panel account, view usage, get configs, QR codes."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.api import XUIClient, XUIError
from bot.config import Settings
from bot.db.models import User
from bot.i18n import t
from bot.keyboards.callbacks import MenuCB, PickClientCB
from bot.keyboards.client import account_kb, client_home, client_menu, pick_client
from bot.middlewares.filters import IsClient
from bot.utils.formatting import compact_bytes, esc, fmt_expiry_card, fmt_quota_card, make_qr_png, progress_bar

router = Router(name="client-account")
router.message.filter(IsClient())
router.callback_query.filter(IsClient())


def render_account(
    client, lang: str = "en", inbound_remarks: list[str] | None = None, tz: ZoneInfo | None = None
) -> str:
    inbounds_label = ", ".join(inbound_remarks) if inbound_remarks else "—"
    quota_label = fmt_quota_card(client.total_gb, client.reset)
    expiry_label = fmt_expiry_card(client.expiry_time, client.reset, tz)
    refresh_ts = datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")

    last_online_str: str | None = None
    if client.last_online > 0:
        try:
            last_online_str = datetime.fromtimestamp(
                client.last_online / 1000, tz=tz
            ).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            pass

    lines = [
        t("acc_email", lang, v=esc(client.email)),
        t("acc_inbounds", lang, v=inbounds_label),
        t("acc_expire", lang, v=expiry_label),
        t("acc_upload", lang, v=compact_bytes(client.up)),
        t("acc_download", lang, v=compact_bytes(client.down)),
        t("acc_total", lang, used=compact_bytes(client.up + client.down), quota=quota_label),
    ]
    if client.total_gb > 0:
        lines.append(t("acc_progress", lang, v=progress_bar(client.up + client.down, client.total_gb)))
    if last_online_str:
        lines.append(t("acc_last_online", lang, v=last_online_str))
    lines += ["", t("refreshed_on", lang, v=refresh_ts)]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Linking
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "link"))
async def cb_link(query: CallbackQuery, user: User, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    try:
        matches = await api.get_clients_by_tgid(user.tg_id)
    except XUIError:
        matches = []

    if len(matches) == 1:
        user.panel_email = matches[0].email
        await user.save()
        await query.message.edit_text(
            t("link_done", lang, email=esc(matches[0].email)),
            reply_markup=client_menu(True, lang=lang),
        )
    elif len(matches) > 1:
        await query.message.edit_text(
            t("pick_account", lang), reply_markup=pick_client(matches, lang)
        )
    else:
        await query.message.edit_text(
            t("link_not_found", lang),
            reply_markup=client_home(lang),
        )
    await query.answer()


@router.callback_query(PickClientCB.filter())
async def cb_pick_client(
    query: CallbackQuery, callback_data: PickClientCB, user: User, lang: str = "en"
) -> None:
    user.panel_email = callback_data.email
    await user.save()
    await query.message.edit_text(
        t("link_done", lang, email=esc(callback_data.email)),
        reply_markup=client_menu(True, lang=lang),
    )
    await query.answer()


@router.callback_query(MenuCB.filter(F.action == "unlink"))
async def cb_unlink(query: CallbackQuery, user: User, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    user.panel_email = None
    await user.save()
    await query.message.edit_text(t("unlink_done", lang), reply_markup=client_menu(False, lang=lang))
    await query.answer()


# --------------------------------------------------------------------------- #
# Account info
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "me"))
async def cb_me(query: CallbackQuery, user: User, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    if not user.panel_email:
        await query.answer(t("account_no_link", lang), show_alert=True)
        return
    await query.answer(t("loading", lang))
    try:
        client = await api.get_client(user.panel_email)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=client_home(lang))
        return
    if client is None:
        await query.message.edit_text(
            t("account_gone", lang),
            reply_markup=client_menu(False, lang=lang),
        )
        user.panel_email = None
        await user.save()
        return

    inbound_remarks: list[str] | None = None
    try:
        options = await api.inbound_options()
        remark_map = {o.id: (o.remark or o.protocol) for o in options}
        remarks = [remark_map.get(i, f"#{i}") for i in client.inbound_ids]
        inbound_remarks = remarks or None
    except Exception:
        pass

    await query.message.edit_text(render_account(client, lang, inbound_remarks, tz), reply_markup=account_kb(lang))


# --------------------------------------------------------------------------- #
# Config links
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "mylinks"))
async def cb_mylinks(query: CallbackQuery, user: User, api: XUIClient, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    if not user.panel_email:
        await query.answer(t("account_no_link", lang), show_alert=True)
        return
    await query.answer(t("loading", lang))
    try:
        links = await api.client_links(user.panel_email)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=client_home(lang))
        return

    parts: list[str] = []
    client = await api.get_client(user.panel_email)
    if client and client.sub_id:
        if settings.sub_base_url:
            sub = settings.sub_base_url.rstrip("/") + "/" + client.sub_id
            parts.append(f"{t('my_sub_label', lang)}\n<code>{esc(sub)}</code>")
        if settings.json_sub_base_url:
            json_sub = settings.json_sub_base_url.rstrip("/") + "/" + client.sub_id
            parts.append(f"{t('json_sub_url_label', lang)}\n<code>{esc(json_sub)}</code>")
    if links:
        parts.append("\n".join(f"<code>{esc(u)}</code>" for u in links))
    if not parts:
        parts.append(t("my_configs_no_links", lang))

    await query.message.edit_text(
        f"{t('my_configs_title', lang)}\n\n" + "\n\n".join(parts),
        reply_markup=client_home(lang),
    )


# --------------------------------------------------------------------------- #
# QR codes
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "myqr"))
async def cb_myqr(query: CallbackQuery, user: User, api: XUIClient, settings: Settings, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    if not user.panel_email:
        await query.answer(t("account_no_link", lang), show_alert=True)
        return

    await query.answer(t("qr_generating", lang))

    try:
        client = await api.get_client(user.panel_email)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=client_home(lang))
        return

    if client is None:
        await query.message.edit_text(
            t("account_gone", lang),
            reply_markup=client_menu(False, lang=lang),
        )
        user.panel_email = None
        await user.save()
        return

    sent_any = False

    if client.sub_id and settings.sub_base_url:
        sub_url = settings.sub_base_url.rstrip("/") + "/" + client.sub_id
        png = make_qr_png(sub_url)
        file = BufferedInputFile(png, filename="subscription_qr.png")
        await query.message.answer_document(file, caption=t("my_qr_sub_caption", lang))
        sent_any = True

    try:
        links = await api.client_links(user.panel_email)
        for i, link in enumerate(links[:5], 1):
            png = make_qr_png(link)
            file = BufferedInputFile(png, filename=f"config_{i}_qr.png")
            await query.message.answer_document(file, caption=t("my_qr_config_caption", lang, n=i))
            sent_any = True
    except XUIError:
        pass

    if not sent_any:
        await query.message.edit_text(t("my_qr_no_data", lang), reply_markup=client_home(lang))
    else:
        await query.message.answer(t("qr_done", lang), reply_markup=client_home(lang))
