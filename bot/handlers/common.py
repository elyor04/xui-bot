"""Shared handlers: /start, /help, /cancel and the home-menu dispatcher."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ErrorEvent, Message

logger = logging.getLogger(__name__)

from bot.api import XUIClient
from bot.db.models import Role, User
from bot.keyboards.admin import admin_menu
from bot.keyboards.callbacks import MenuCB, PickModeCB
from bot.keyboards.client import client_menu, mode_picker, pick_client
from bot.utils.formatting import esc

router = Router(name="common")


def home_text(user: User) -> str:
    if user.effective_role == Role.ADMIN:
        return (
            f"👋 <b>Admin panel</b>\n"
            f"Signed in as <code>{esc(user.full_name)}</code>.\n\n"
            f"Manage clients, inbounds and the server below."
        )
    if user.is_linked:
        return (
            f"👋 Welcome back, <b>{esc(user.full_name)}</b>.\n"
            f"Your account is linked to <code>{esc(user.panel_email)}</code>."
        )
    return (
        f"👋 Welcome, <b>{esc(user.full_name)}</b>.\n\n"
        f"Tap <b>Link my account</b> to connect."
    )


def home_markup(user: User):
    if user.effective_role == Role.ADMIN:
        return admin_menu(switch=user.is_admin)
    return client_menu(user.is_linked, switch=user.is_admin)


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, state: FSMContext, api: XUIClient) -> None:
    await state.clear()

    if user.role == Role.ADMIN:
        # Show mode picker when admin hasn't picked a mode yet and has client accounts.
        if user.active_role is None:
            client_emails: list[str] = (
                [user.panel_email] if user.panel_email
                else [c.email for c in await _fetch_matches(api, user.tg_id)]
            )
            if client_emails:
                await message.answer(
                    "👋 How would you like to use the bot?",
                    reply_markup=mode_picker(client_emails),
                )
                return
    else:
        # Regular client: auto-link if exactly one panel account matches their TG ID.
        if not user.is_linked:
            matches = await _fetch_matches(api, user.tg_id)
            if len(matches) == 1:
                user.panel_email = matches[0].email
                await user.save()
            elif len(matches) > 1:
                await message.answer(
                    "👤 Which account is yours?", reply_markup=pick_client(matches)
                )
                return

    await message.answer(home_text(user), reply_markup=home_markup(user))


async def _fetch_matches(api: XUIClient, tg_id: int):
    try:
        return await api.get_clients_by_tgid(tg_id)
    except Exception:  # noqa: BLE001
        return []


# ---------------------------------------------------------------------------
# Mode switching (admin ↔ client) — no role filter, works from any context
# ---------------------------------------------------------------------------
@router.callback_query(PickModeCB.filter(F.action == "admin"))
async def cb_mode_admin(query: CallbackQuery, user: User) -> None:
    user.active_role = Role.ADMIN
    await user.save()
    await query.message.edit_text(home_text(user), reply_markup=home_markup(user))
    await query.answer()


@router.callback_query(PickModeCB.filter(F.action == "client"))
async def cb_mode_client(
    query: CallbackQuery, callback_data: PickModeCB, user: User
) -> None:
    user.active_role = Role.CLIENT
    user.panel_email = callback_data.email
    await user.save()
    await query.message.edit_text(home_text(user), reply_markup=home_markup(user))
    await query.answer()


@router.callback_query(PickModeCB.filter(F.action == "switch"))
async def cb_mode_switch(query: CallbackQuery, user: User, api: XUIClient) -> None:
    client_emails: list[str] = (
        [user.panel_email] if user.panel_email
        else [c.email for c in await _fetch_matches(api, user.tg_id)]
    )
    if not client_emails:
        await query.answer(
            "No client accounts are assigned to your Telegram ID.", show_alert=True
        )
        return
    await query.message.edit_text(
        "👋 How would you like to use the bot?",
        reply_markup=mode_picker(client_emails),
    )
    await query.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, user: User) -> None:
    if user.is_admin:
        text = (
            "<b>Admin commands</b>\n"
            "/start – open the menu\n"
            "/find &lt;email&gt; – jump straight to a client\n"
            "/cancel – abort the current action\n\n"
            "Everything else is driven by the inline buttons."
        )
    else:
        text = (
            "<b>Commands</b>\n"
            "/start – open the menu\n"
            "/cancel – abort the current action\n\n"
            "Use the buttons to link your account and view usage."
        )
    await message.answer(text)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, user: User) -> None:
    await state.clear()
    await message.answer("Cancelled.", reply_markup=home_markup(user))


@router.callback_query(MenuCB.filter(F.action == "home"))
async def cb_home(query: CallbackQuery, user: User, state: FSMContext) -> None:
    await state.clear()
    await query.message.edit_text(home_text(user), reply_markup=home_markup(user))
    await query.answer()


@router.callback_query(MenuCB.filter(F.action == "noop"))
async def cb_noop(query: CallbackQuery) -> None:
    await query.answer()


@router.error()
async def handle_error(event: ErrorEvent) -> None:
    exc = event.exception
    if isinstance(exc, TelegramBadRequest) and "message is not modified" in str(exc):
        # User hit Refresh before anything changed — silently acknowledge.
        cq = event.update.callback_query
        if cq:
            try:
                await cq.answer()
            except Exception:
                pass
        return
    logger.exception("Unhandled update error", exc_info=exc)
