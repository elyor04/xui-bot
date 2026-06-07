"""Inline keyboards for the client (end-user) side."""
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.callbacks import MenuCB, PickClientCB, PickModeCB


def client_menu(linked: bool, switch: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if linked:
        kb.button(text="📈 My account", callback_data=MenuCB(action="me"))
        kb.button(text="🔗 My configs", callback_data=MenuCB(action="mylinks"))
        kb.button(text="📷 My QR", callback_data=MenuCB(action="myqr"))
        kb.button(text="🔌 Unlink", callback_data=MenuCB(action="unlink"))
        kb.adjust(2, 2)
    else:
        kb.button(text="🔗 Link my account", callback_data=MenuCB(action="link"))
        kb.adjust(1)
    if switch:
        sw = InlineKeyboardBuilder()
        sw.button(text="⚙️ Switch to admin", callback_data=PickModeCB(action="admin"))
        kb.attach(sw)
    return kb.as_markup()


def mode_picker(client_emails: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⚙️ Admin panel", callback_data=PickModeCB(action="admin"))
    for email in client_emails:
        kb.button(text=f"👤 {email}", callback_data=PickModeCB(action="client", email=email))
    kb.adjust(1)
    return kb.as_markup()


def pick_client(clients: list) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in clients:
        kb.button(text=c.email, callback_data=PickClientCB(email=c.email))
    kb.button(text="✖️ Cancel", callback_data=MenuCB(action="home"))
    kb.adjust(1)
    return kb.as_markup()


def client_home() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    return kb.as_markup()


def account_kb() -> InlineKeyboardMarkup:
    """Keyboard shown on the account info ("me") view: refresh + home."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Refresh", callback_data=MenuCB(action="me"))
    kb.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()
