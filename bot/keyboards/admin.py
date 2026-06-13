"""Inline keyboards for the admin side."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api.models import Client, InboundOption
from bot.i18n import t
from bot.keyboards.callbacks import (
    ClientCB,
    ConfirmCB,
    InbPickCB,
    LangCB,
    MenuCB,
    NumpadCB,
    PageCB,
    PickModeCB,
    QuickPickCB,
)
from aiogram.filters.callback_data import CallbackData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _footer(lang: str = "en", back_cb=None) -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    if back_cb:
        b.button(text=t("btn_back", lang), callback_data=back_cb)
    b.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    b.adjust(2 if back_cb else 1)
    return b


# ---------------------------------------------------------------------------
# Main admin menu
# ---------------------------------------------------------------------------

def admin_menu(switch: bool = False, lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_sorted_traffic", lang), callback_data=MenuCB(action="sorted_report"))
    kb.button(text=t("btn_server", lang), callback_data=MenuCB(action="server"))
    kb.button(text=t("btn_reset_all", lang), callback_data=MenuCB(action="reset_all"))
    kb.button(text=t("btn_backup", lang), callback_data=MenuCB(action="backup"))
    kb.button(text=t("btn_restart_xray", lang), callback_data=MenuCB(action="restart"))
    kb.button(text=t("btn_stop_xray", lang), callback_data=MenuCB(action="stop_xray"))
    kb.button(text=t("btn_deldepleted", lang), callback_data=MenuCB(action="deldepleted"))
    kb.button(text=t("btn_inbounds", lang), callback_data=MenuCB(action="inbounds"))
    kb.button(text=t("btn_deplete_soon", lang), callback_data=MenuCB(action="deplete_soon"))
    kb.button(text=t("btn_commands", lang), callback_data=MenuCB(action="commands"))
    kb.button(text=t("btn_online", lang), callback_data=MenuCB(action="online"))
    kb.button(text=t("btn_clients", lang), callback_data=MenuCB(action="clients"))
    kb.button(text=t("btn_create_client", lang), callback_data=MenuCB(action="create"))
    kb.adjust(1, 2, 2, 2, 2, 2, 2)
    extras = InlineKeyboardBuilder()
    extras.button(text=t("btn_language", lang), callback_data=MenuCB(action="language"))
    if switch:
        extras.button(text=t("btn_switch_to_client", lang), callback_data=PickModeCB(action="switch"))
    extras.adjust(2 if switch else 1)
    kb.attach(extras)
    return kb.as_markup()


def back_home(lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    return kb.as_markup()


def find_prompt_kb(lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_search_inline", lang), switch_inline_query_current_chat="")
    kb.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    kb.adjust(1)
    return kb.as_markup()


def back_home_refresh(refresh_cb: CallbackData, lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_refresh", lang), callback_data=refresh_cb)
    kb.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()


def ip_log_kb(email: str, lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_refresh", lang), callback_data=ClientCB(action="ips", email=email))
    kb.button(text=t("btn_clear_ips", lang), callback_data=ClientCB(action="clearips", email=email))
    kb.button(text=t("btn_back", lang), callback_data=ClientCB(action="view", email=email))
    kb.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    kb.adjust(2, 2)
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Inbound picker (create wizard)
# ---------------------------------------------------------------------------

def inbound_picker(
    options: list[InboundOption], selected: set[int], lang: str = "en"
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for opt in options:
        mark = "✅ " if opt.id in selected else "▫️ "
        label = f"{mark}{opt.remark or opt.protocol}:{opt.port} (#{opt.id})"
        kb.button(text=label, callback_data=InbPickCB(action="toggle", inbound_id=opt.id))
    kb.adjust(1)
    done = InlineKeyboardBuilder()
    done.button(text=t("btn_continue", lang), callback_data=InbPickCB(action="done"))
    done.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    done.adjust(2)
    kb.attach(done)
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Client card
# ---------------------------------------------------------------------------

def client_card(client: Client, lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    e = client.email
    toggle = t("btn_disable", lang) if client.enable else t("btn_enable", lang)
    kb.button(text=t("btn_reset_traffic", lang), callback_data=ClientCB(action="reset", email=e))
    kb.button(text=t("btn_extend_days", lang), callback_data=ClientCB(action="extend", email=e))
    kb.button(text=t("btn_set_quota", lang), callback_data=ClientCB(action="set_quota", email=e))
    kb.button(text=t("btn_set_expiry", lang), callback_data=ClientCB(action="set_expiry", email=e))
    kb.button(text=t("btn_ips", lang), callback_data=ClientCB(action="ips", email=e))
    kb.button(text=t("btn_clear_ips", lang), callback_data=ClientCB(action="clearips", email=e))
    kb.button(text=t("btn_ip_limit", lang), callback_data=ClientCB(action="ip_limit", email=e))
    kb.button(text=toggle, callback_data=ClientCB(action="toggle", email=e))
    kb.button(text=t("btn_sub_url", lang), callback_data=ClientCB(action="sublinks", email=e))
    kb.button(text=t("btn_ind_links", lang), callback_data=ClientCB(action="links", email=e))
    kb.button(text=t("btn_qr", lang), callback_data=ClientCB(action="qr", email=e))
    kb.button(text=t("btn_delete", lang), callback_data=ClientCB(action="del", email=e))
    kb.button(text=t("btn_set_tgid", lang), callback_data=ClientCB(action="set_tgid", email=e))
    kb.button(text=t("btn_back", lang), callback_data=MenuCB(action="clients"))
    kb.button(text=t("btn_refresh", lang), callback_data=ClientCB(action="refresh", email=e))
    kb.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    kb.adjust(2, 2, 2, 2, 3, 2, 3)
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Clients list
# ---------------------------------------------------------------------------

def online_clients_list(emails: list[str], lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for email in emails:
        kb.button(text=f"🟢 {email}", callback_data=ClientCB(action="view", email=email))
    kb.adjust(1)
    footer = InlineKeyboardBuilder()
    footer.button(text=t("btn_refresh", lang), callback_data=MenuCB(action="online"))
    footer.button(text=t("btn_menu", lang), callback_data=MenuCB(action="home"))
    footer.adjust(2)
    kb.attach(footer)
    return kb.as_markup()


def inbound_filter(options: list[InboundOption], lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_all_clients", lang), callback_data=PageCB(target="clients", page=0, inbound_id=-1))
    for opt in options:
        label = f"📦 {opt.remark or opt.protocol}:{opt.port}"
        kb.button(text=label, callback_data=PageCB(target="clients", page=0, inbound_id=opt.id))
    kb.adjust(1)
    kb.attach(_footer(lang))
    return kb.as_markup()


def clients_list(
    clients: list[Client], page: int, pages: int, inbound_id: int = -1, lang: str = "en"
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in clients:
        status = "🟢" if c.enable else "🔴"
        kb.button(text=f"{status} {c.email}", callback_data=ClientCB(action="view", email=c.email))
    kb.adjust(1)
    nav = InlineKeyboardBuilder()
    if page > 0:
        nav.button(text="◀️", callback_data=PageCB(target="clients", page=page - 1, inbound_id=inbound_id))
    nav.button(text=f"{page + 1}/{pages}", callback_data=MenuCB(action="noop"))
    if page < pages - 1:
        nav.button(text="▶️", callback_data=PageCB(target="clients", page=page + 1, inbound_id=inbound_id))
    nav.adjust(3)
    kb.attach(nav)
    kb.attach(_footer(lang, back_cb=MenuCB(action="clients")))
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Confirm dialogs
# ---------------------------------------------------------------------------

def confirm_delete(email: str, lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_yes_delete", lang), callback_data=ConfirmCB(action="yes", scope="del", arg=email))
    kb.button(text=t("btn_cancel", lang), callback_data=ClientCB(action="view", email=email))
    kb.adjust(2)
    return kb.as_markup()


def confirm_create(lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=t("btn_yes_create", lang), callback_data=ConfirmCB(action="yes", scope="create"))
    kb.button(text=t("btn_cancel", lang), callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()


def confirm_reset_all(lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=t("btn_yes_reset_all", lang), callback_data=ConfirmCB(action="yes", scope="reset_all")
    )
    kb.button(text=t("btn_cancel", lang), callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()


def confirm_stop_xray(lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text=t("btn_yes_stop_xray", lang), callback_data=ConfirmCB(action="yes", scope="stop_xray")
    )
    kb.button(text=t("btn_cancel", lang), callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Quick-pick keyboards  (days / quota / IP-limit presets)
# ---------------------------------------------------------------------------

_DAY_PRESETS = [7, 14, 30, 90, 180, 365]


def quick_days(email: str = "", field: str = "extend", lang: str = "en") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for d in _DAY_PRESETS:
        kb.button(text=f"{d}d", callback_data=QuickPickCB(field=field, value=d, email=email))
    unlimited_label = t("extend_remove_expiry_btn", lang) if field == "extend" else t("no_expiry_btn", lang)
    kb.button(text=unlimited_label, callback_data=QuickPickCB(field=field, value=0, email=email))
    if email:
        kb.button(text=t("btn_custom", lang), callback_data=NumpadCB(field=field, email=email, val=0, digit=-2))
    else:
        kb.button(text=t("btn_custom", lang), callback_data=QuickPickCB(field=field, value=-1, email=email))
    kb.adjust(3, 3, 2)
    back_cb = ClientCB(action="view", email=email) if email else None
    kb.attach(_footer(lang, back_cb=back_cb))
    return kb.as_markup()


def quick_quota(email: str = "", lang: str = "en") -> InlineKeyboardMarkup:
    field = "wiz_quota" if not email else "quota"
    presets = [(0, "∞"), (1, "1 GB"), (5, "5 GB"), (10, "10 GB"),
               (20, "20 GB"), (30, "30 GB"), (50, "50 GB"), (100, "100 GB")]
    kb = InlineKeyboardBuilder()
    for val, label in presets:
        kb.button(text=label, callback_data=QuickPickCB(field=field, value=val, email=email))
    if email:
        kb.button(text=t("btn_custom", lang), callback_data=NumpadCB(field=field, email=email, val=0, digit=-2))
    else:
        kb.button(text=t("btn_custom", lang), callback_data=QuickPickCB(field=field, value=-1, email=email))
    kb.adjust(3, 3, 3)
    back_cb = ClientCB(action="view", email=email) if email else None
    kb.attach(_footer(lang, back_cb=back_cb))
    return kb.as_markup()


def quick_iplimit(email: str = "", lang: str = "en") -> InlineKeyboardMarkup:
    presets = [(0, "∞"), (1, "1"), (2, "2"), (3, "3"), (5, "5"), (10, "10")]
    kb = InlineKeyboardBuilder()
    for val, label in presets:
        kb.button(text=label, callback_data=QuickPickCB(field="iplimit", value=val, email=email))
    if email:
        kb.button(text=t("btn_custom", lang), callback_data=NumpadCB(field="iplimit", email=email, val=0, digit=-2))
    else:
        kb.button(text=t("btn_custom", lang), callback_data=QuickPickCB(field="iplimit", value=-1, email=email))
    kb.adjust(3, 3, 1)
    back_cb = ClientCB(action="view", email=email) if email else None
    kb.attach(_footer(lang, back_cb=back_cb))
    return kb.as_markup()


def numpad_kb(field: str, email: str, val: int, unit_label: str, lang: str = "en") -> InlineKeyboardMarkup:
    """Inline numpad keyboard for entering a custom numeric value."""
    kb = InlineKeyboardBuilder()
    confirm_text = f"✅  {val} {unit_label}"
    kb.button(text=confirm_text, callback_data=NumpadCB(field=field, email=email, val=val, digit=100))
    for d in range(1, 10):
        kb.button(text=str(d), callback_data=NumpadCB(field=field, email=email, val=val, digit=d))
    kb.button(text="∞", callback_data=NumpadCB(field=field, email=email, val=0, digit=100))
    kb.button(text="0", callback_data=NumpadCB(field=field, email=email, val=val, digit=0))
    kb.button(text="⬅️", callback_data=NumpadCB(field=field, email=email, val=val, digit=-1))
    kb.button(text="🔄", callback_data=NumpadCB(field=field, email=email, val=val, digit=-2))
    kb.button(text=t("btn_cancel", lang), callback_data=ClientCB(action="view", email=email))
    kb.adjust(1, 3, 3, 3, 3, 2)
    return kb.as_markup()
