"""Inline keyboards for the client (end-user) side."""
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.i18n import LANGS, t
from bot.keyboards.callbacks import LangCB, MenuCB, PickClientCB, PickModeCB


def client_menu(linked: bool, switch: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if linked:
        kb.button(text=t("btn_my_account", lang), callback_data=MenuCB(action="me"))
        kb.button(text=t("btn_my_configs", lang), callback_data=MenuCB(action="mylinks"))
        kb.button(text=t("btn_my_qr", lang), callback_data=MenuCB(action="myqr"))
        kb.button(text=t("btn_unlink", lang), callback_data=MenuCB(action="unlink"))
        kb.adjust(2, 2)
    else:
        kb.button(text=t("btn_link_account", lang), callback_data=MenuCB(action="link"))
        kb.adjust(1)
    extras = InlineKeyboardBuilder()
    if switch:
        extras.button(text=t("btn_switch_to_admin", lang), callback_data=PickModeCB(action="admin"))
    extras.button(text=t("btn_language", lang), callback_data=MenuCB(action="language"))
    extras.adjust(1)
    kb.attach(extras)
    return kb.as_markup()


def mode_picker(client_emails: list[str], lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_admin_panel", lang), callback_data=PickModeCB(action="admin"))
    for email in client_emails:
        kb.button(text=f"👤 {email}", callback_data=PickModeCB(action="client", email=email))
    kb.adjust(1)
    return kb.as_markup()


def pick_client(clients: list, lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in clients:
        kb.button(text=c.email, callback_data=PickClientCB(email=c.email))
    kb.button(text=t("btn_cancel", lang), callback_data=MenuCB(action="home"))
    kb.adjust(1)
    return kb.as_markup()


def client_home(lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    return kb.as_markup()


def account_kb(lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_refresh", lang), callback_data=MenuCB(action="me"))
    kb.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()


def language_picker() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for code, name in LANGS.items():
        kb.button(text=name, callback_data=LangCB(code=code))
    kb.adjust(1)
    return kb.as_markup()
