"""Client (end-user) side: link to a panel account, view usage, get configs, QR codes."""
from __future__ import annotations

import io
from datetime import datetime

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.api import XUIClient, XUIError
from bot.config import Settings
from bot.db.models import User
from bot.keyboards.callbacks import MenuCB, PickClientCB
from bot.keyboards.client import account_kb, client_home, client_menu, pick_client
from bot.middlewares.filters import IsClient
from bot.utils.formatting import LOCAL_TZ, compact_bytes, esc, fmt_expiry_card, fmt_quota_card

router = Router(name="client-account")
router.message.filter(IsClient())
router.callback_query.filter(IsClient())

# ---------------------------------------------------------------------------
# Optional QR support — degrades gracefully when qrcode/Pillow not installed
# ---------------------------------------------------------------------------
try:
    import qrcode  # type: ignore

    def _make_qr_png(data: str) -> bytes:
        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    _HAS_QR = True
except ImportError:
    _HAS_QR = False

    def _make_qr_png(data: str) -> bytes:  # type: ignore[misc]
        return b""


def render_account(client, inbound_remarks: list[str] | None = None) -> str:
    inbounds_label = ", ".join(inbound_remarks) if inbound_remarks else "—"
    quota_label = fmt_quota_card(client.total_gb, client.reset)
    expiry_label = fmt_expiry_card(client.expiry_time, client.reset)
    refresh_ts = datetime.now(tz=LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

    last_online_str: str | None = None
    if client.last_online > 0:
        try:
            last_online_str = datetime.fromtimestamp(
                client.last_online / 1000, tz=LOCAL_TZ
            ).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            pass

    lines = [
        f"📧 Email: {esc(client.email)}",
        f"🔗 Inbounds: {inbounds_label}",
        f"📅 Expire Date: {expiry_label}",
        f"🔼 Upload: ↑{compact_bytes(client.up)}",
        f"🔽 Download: ↓{compact_bytes(client.down)}",
        f"📊 Total: ↑↓{compact_bytes(client.up + client.down)} / {quota_label}",
    ]
    if last_online_str:
        lines.append(f"🔙 Last online: {last_online_str}")
    lines += ["", f"📋🔄 Refreshed On: {refresh_ts}"]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Linking
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "link"))
async def cb_link(query: CallbackQuery, user: User, api: XUIClient) -> None:
    try:
        matches = await api.get_clients_by_tgid(user.tg_id)
    except XUIError:
        matches = []

    if len(matches) == 1:
        user.panel_email = matches[0].email
        await user.save()
        await query.message.edit_text(
            f"✅ Linked to <code>{esc(matches[0].email)}</code>.", reply_markup=client_menu(True)
        )
    elif len(matches) > 1:
        await query.message.edit_text(
            "👤 Which account is yours?", reply_markup=pick_client(matches)
        )
    else:
        await query.message.edit_text(
            "❌ Your Telegram ID is not assigned to any account yet. Contact your provider.",
            reply_markup=client_home(),
        )
    await query.answer()


@router.callback_query(PickClientCB.filter())
async def cb_pick_client(
    query: CallbackQuery, callback_data: PickClientCB, user: User
) -> None:
    user.panel_email = callback_data.email
    await user.save()
    await query.message.edit_text(
        f"✅ Linked to <code>{esc(callback_data.email)}</code>.", reply_markup=client_menu(True)
    )
    await query.answer()


@router.callback_query(MenuCB.filter(F.action == "unlink"))
async def cb_unlink(query: CallbackQuery, user: User) -> None:
    user.panel_email = None
    await user.save()
    await query.message.edit_text("🔌 Account unlinked.", reply_markup=client_menu(False))
    await query.answer()


# --------------------------------------------------------------------------- #
# Account info
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "me"))
async def cb_me(query: CallbackQuery, user: User, api: XUIClient) -> None:
    if not user.panel_email:
        await query.answer("Link your account first.", show_alert=True)
        return
    await query.answer("Loading…")
    try:
        client = await api.get_client(user.panel_email)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=client_home())
        return
    if client is None:
        await query.message.edit_text(
            "Your linked account no longer exists. Please re-link.",
            reply_markup=client_menu(False),
        )
        user.panel_email = None
        await user.save()
        return

    inbound_remarks: list[str] | None = None
    try:
        inbounds = await api.list_inbounds()
        remark_map = {ib.id: (ib.remark or ib.protocol) for ib in inbounds}
        remarks = [remark_map.get(i, f"#{i}") for i in client.inbound_ids]
        inbound_remarks = remarks or None
    except Exception:
        pass

    await query.message.edit_text(render_account(client, inbound_remarks), reply_markup=account_kb())


# --------------------------------------------------------------------------- #
# Config links
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "mylinks"))
async def cb_mylinks(query: CallbackQuery, user: User, api: XUIClient, settings: Settings) -> None:
    if not user.panel_email:
        await query.answer("Link your account first.", show_alert=True)
        return
    await query.answer("Loading…")
    try:
        links = await api.client_links(user.panel_email)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=client_home())
        return

    parts: list[str] = []
    client = await api.get_client(user.panel_email)
    if client and client.sub_id and settings.sub_base_url:
        sub = settings.sub_base_url.rstrip("/") + "/" + client.sub_id
        parts.append(f"<b>Subscription</b>\n<code>{esc(sub)}</code>")
    if links:
        parts.append("\n".join(f"<code>{esc(u)}</code>" for u in links))
    if not parts:
        parts.append("No config links are available for your account.")

    await query.message.edit_text(
        "🔗 <b>Your configs</b>\n\n" + "\n\n".join(parts), reply_markup=client_home()
    )


# --------------------------------------------------------------------------- #
# QR codes
# --------------------------------------------------------------------------- #
@router.callback_query(MenuCB.filter(F.action == "myqr"))
async def cb_myqr(query: CallbackQuery, user: User, api: XUIClient, settings: Settings) -> None:
    """Generate QR codes for the user's own subscription URL and individual links."""
    if not user.panel_email:
        await query.answer("Link your account first.", show_alert=True)
        return

    if not _HAS_QR:
        await query.answer(
            "QR generation unavailable. Install qrcode[pil] and restart the bot.",
            show_alert=True,
        )
        return

    await query.answer("Generating QR…")

    try:
        client = await api.get_client(user.panel_email)
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=client_home())
        return

    if client is None:
        await query.message.edit_text(
            "Your linked account no longer exists. Please re-link.",
            reply_markup=client_menu(False),
        )
        user.panel_email = None
        await user.save()
        return

    sent_any = False

    # Sub URL QR
    if client.sub_id and settings.sub_base_url:
        sub_url = settings.sub_base_url.rstrip("/") + "/" + client.sub_id
        png = _make_qr_png(sub_url)
        file = BufferedInputFile(png, filename="subscription_qr.png")
        await query.message.answer_document(file, caption="📷 Your subscription QR code")
        sent_any = True

    # Individual links QRs (first 5)
    try:
        links = await api.client_links(user.panel_email)
        for i, link in enumerate(links[:5], 1):
            png = _make_qr_png(link)
            file = BufferedInputFile(png, filename=f"config_{i}_qr.png")
            await query.message.answer_document(file, caption=f"📷 Config #{i}")
            sent_any = True
    except XUIError:
        pass

    if not sent_any:
        await query.message.edit_text(
            "No QR data available.\n"
            "Set <code>SUB_BASE_URL</code> in your bot config or ask your provider for links.",
            reply_markup=client_home(),
        )
    else:
        await query.message.answer("✅ Done.", reply_markup=client_home())
