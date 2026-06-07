"""Shared handlers: /start, /help, /cancel, home-menu dispatcher, language selection."""
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
from bot.i18n import t
from bot.keyboards.admin import admin_menu
from bot.keyboards.callbacks import LangCB, MenuCB, PickModeCB
from bot.keyboards.client import client_menu, language_picker, mode_picker, pick_client
from bot.utils.formatting import esc

router = Router(name="common")


def home_text(user: User, lang: str = "en") -> str:
    if user.effective_role == Role.ADMIN:
        return t("home_admin", lang, name=esc(user.full_name))
    if user.is_linked:
        return t("home_client_linked", lang, name=esc(user.full_name), email=esc(user.panel_email))
    return t("home_client_unlinked", lang, name=esc(user.full_name))


def home_markup(user: User, lang: str = "en"):
    if user.effective_role == Role.ADMIN:
        return admin_menu(switch=user.is_admin, lang=lang)
    return client_menu(user.is_linked, switch=user.is_admin, lang=lang)


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, state: FSMContext, api: XUIClient, lang: str = "en") -> None:
    await state.clear()

    if user.role == Role.ADMIN:
        if user.active_role is None:
            client_emails: list[str] = (
                [user.panel_email] if user.panel_email
                else [c.email for c in await _fetch_matches(api, user.tg_id)]
            )
            if client_emails:
                await message.answer(
                    t("mode_picker_prompt", lang),
                    reply_markup=mode_picker(client_emails, lang),
                )
                return
    else:
        if not user.is_linked:
            matches = await _fetch_matches(api, user.tg_id)
            if len(matches) == 1:
                user.panel_email = matches[0].email
                await user.save()
            elif len(matches) > 1:
                await message.answer(
                    t("pick_account", lang), reply_markup=pick_client(matches, lang)
                )
                return

    await message.answer(home_text(user, lang), reply_markup=home_markup(user, lang))


async def _fetch_matches(api: XUIClient, tg_id: int):
    try:
        return await api.get_clients_by_tgid(tg_id)
    except Exception:  # noqa: BLE001
        return []


# ---------------------------------------------------------------------------
# Mode switching (admin ↔ client)
# ---------------------------------------------------------------------------
@router.callback_query(PickModeCB.filter(F.action == "admin"))
async def cb_mode_admin(query: CallbackQuery, user: User, lang: str = "en") -> None:
    user.active_role = Role.ADMIN
    await user.save()
    await query.message.edit_text(home_text(user, lang), reply_markup=home_markup(user, lang))
    await query.answer()


@router.callback_query(PickModeCB.filter(F.action == "client"))
async def cb_mode_client(
    query: CallbackQuery, callback_data: PickModeCB, user: User, lang: str = "en"
) -> None:
    user.active_role = Role.CLIENT
    user.panel_email = callback_data.email
    await user.save()
    await query.message.edit_text(home_text(user, lang), reply_markup=home_markup(user, lang))
    await query.answer()


@router.callback_query(PickModeCB.filter(F.action == "switch"))
async def cb_mode_switch(query: CallbackQuery, user: User, api: XUIClient, lang: str = "en") -> None:
    client_emails: list[str] = (
        [user.panel_email] if user.panel_email
        else [c.email for c in await _fetch_matches(api, user.tg_id)]
    )
    if not client_emails:
        await query.answer(t("no_client_accounts", lang), show_alert=True)
        return
    await query.message.edit_text(
        t("mode_picker_prompt", lang),
        reply_markup=mode_picker(client_emails, lang),
    )
    await query.answer()


# ---------------------------------------------------------------------------
# Language selection
# ---------------------------------------------------------------------------
@router.callback_query(MenuCB.filter(F.action == "language"))
async def cb_language(query: CallbackQuery, lang: str = "en") -> None:
    await query.message.edit_text(
        t("choose_language", lang),
        reply_markup=language_picker(),
    )
    await query.answer()


@router.callback_query(LangCB.filter())
async def cb_set_lang(
    query: CallbackQuery, callback_data: LangCB, user: User
) -> None:
    user.language = callback_data.code
    await user.save()
    lang = callback_data.code
    await query.message.edit_text(
        t("language_set", lang),
        reply_markup=home_markup(user, lang),
    )
    await query.answer()


# ---------------------------------------------------------------------------
# Help / cancel / home / noop
# ---------------------------------------------------------------------------
@router.message(Command("help"))
async def cmd_help(message: Message, user: User, lang: str = "en") -> None:
    text = t("help_admin", lang) if user.is_admin else t("help_client", lang)
    await message.answer(text)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, user: User, lang: str = "en") -> None:
    await state.clear()
    await message.answer(t("cancelled", lang), reply_markup=home_markup(user, lang))


@router.callback_query(MenuCB.filter(F.action == "home"))
async def cb_home(query: CallbackQuery, user: User, state: FSMContext, lang: str = "en") -> None:
    await state.clear()
    await query.message.edit_text(home_text(user, lang), reply_markup=home_markup(user, lang))
    await query.answer()


@router.callback_query(MenuCB.filter(F.action == "noop"))
async def cb_noop(query: CallbackQuery) -> None:
    await query.answer()


@router.error()
async def handle_error(event: ErrorEvent) -> None:
    exc = event.exception
    if isinstance(exc, TelegramBadRequest) and "message is not modified" in str(exc):
        cq = event.update.callback_query
        if cq:
            try:
                await cq.answer()
            except Exception:
                pass
        return
    logger.exception("Unhandled update error", exc_info=exc)
