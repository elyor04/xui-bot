"""Inline keyboards for the admin side."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.api.models import Client, InboundOption
from bot.keyboards.callbacks import ClientCB, ConfirmCB, InbPickCB, MenuCB, PageCB, PickModeCB, QuickPickCB
from aiogram.filters.callback_data import CallbackData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _footer(back_cb=None) -> InlineKeyboardBuilder:
    b = InlineKeyboardBuilder()
    if back_cb:
        b.button(text="⬅️ Back", callback_data=back_cb)
    b.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    b.adjust(2 if back_cb else 1)
    return b


# ---------------------------------------------------------------------------
# Main admin menu
# ---------------------------------------------------------------------------

def admin_menu(switch: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Sorted Traffic Report", callback_data=MenuCB(action="sorted_report"))
    kb.button(text="📈 Server", callback_data=MenuCB(action="server"))
    kb.button(text="🔄 Reset All Traffics", callback_data=MenuCB(action="reset_all"))
    kb.button(text="💾 Backup", callback_data=MenuCB(action="backup"))
    kb.button(text="⚡ Restart Xray", callback_data=MenuCB(action="restart"))
    kb.button(text="📦 Inbounds", callback_data=MenuCB(action="inbounds"))
    kb.button(text="⚠️ Deplete Soon", callback_data=MenuCB(action="deplete_soon"))
    kb.button(text="📋 Commands", callback_data=MenuCB(action="commands"))
    kb.button(text="🟢 Online", callback_data=MenuCB(action="online"))
    kb.button(text="👥 Clients", callback_data=MenuCB(action="clients"))
    kb.button(text="➕ Create client", callback_data=MenuCB(action="create"))
    kb.adjust(1, 2, 2, 2, 2, 2)
    if switch:
        sw = InlineKeyboardBuilder()
        sw.button(text="👤 Switch to client", callback_data=PickModeCB(action="switch"))
        kb.attach(sw)
    return kb.as_markup()


def back_home() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    return kb.as_markup()


def back_home_refresh(refresh_cb: CallbackData) -> InlineKeyboardMarkup:
    """Two-button footer: [🔄 Refresh] [🏠 Menu]."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Refresh", callback_data=refresh_cb)
    kb.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()


def ip_log_kb(email: str) -> InlineKeyboardMarkup:
    """Keyboard for the IP log view: refresh, clear, back to client card, home."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Refresh", callback_data=ClientCB(action="ips", email=email))
    kb.button(text="🧽 Clear IPs", callback_data=ClientCB(action="clearips", email=email))
    kb.button(text="⬅️ Back", callback_data=ClientCB(action="view", email=email))
    kb.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    kb.adjust(2, 2)
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Inbound picker (create wizard)
# ---------------------------------------------------------------------------

def inbound_picker(
    options: list[InboundOption], selected: set[int]
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for opt in options:
        mark = "✅ " if opt.id in selected else "▫️ "
        label = f"{mark}{opt.remark or opt.protocol}:{opt.port} (#{opt.id})"
        kb.button(text=label, callback_data=InbPickCB(action="toggle", inbound_id=opt.id))
    kb.adjust(1)
    done = InlineKeyboardBuilder()
    done.button(text="➡️ Continue", callback_data=InbPickCB(action="done"))
    done.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    done.adjust(2)
    kb.attach(done)
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Client card
# ---------------------------------------------------------------------------

def client_card(client: Client) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    e = client.email
    toggle = "⏸ Disable" if client.enable else "▶️ Enable"
    # Row 1
    kb.button(text="♻️ Reset traffic", callback_data=ClientCB(action="reset", email=e))
    kb.button(text="➕ Extend days", callback_data=ClientCB(action="extend", email=e))
    # Row 2
    kb.button(text="💽 Set quota", callback_data=ClientCB(action="set_quota", email=e))
    kb.button(text="📅 Set expiry", callback_data=ClientCB(action="set_expiry", email=e))
    # Row 3
    kb.button(text="🌐 IPs", callback_data=ClientCB(action="ips", email=e))
    kb.button(text="🧽 Clear IPs", callback_data=ClientCB(action="clearips", email=e))
    # Row 4
    kb.button(text="🔢 IP limit", callback_data=ClientCB(action="ip_limit", email=e))
    kb.button(text=toggle, callback_data=ClientCB(action="toggle", email=e))
    # Row 5
    kb.button(text="🔗 Sub URL", callback_data=ClientCB(action="sublinks", email=e))
    kb.button(text="🔗 Ind. links", callback_data=ClientCB(action="links", email=e))
    kb.button(text="📷 QR", callback_data=ClientCB(action="qr", email=e))
    # Row 6
    kb.button(text="🗑 Delete", callback_data=ClientCB(action="del", email=e))
    kb.button(text="👤 Set TG ID", callback_data=ClientCB(action="set_tgid", email=e))
    # Row 7
    kb.button(text="⬅️ Back", callback_data=MenuCB(action="clients"))
    kb.button(text="🔄 Refresh", callback_data=ClientCB(action="refresh", email=e))
    kb.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    kb.adjust(2, 2, 2, 2, 3, 2, 3)
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Clients list
# ---------------------------------------------------------------------------

def online_clients_list(emails: list[str]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for email in emails:
        kb.button(text=f"🟢 {email}", callback_data=ClientCB(action="view", email=email))
    kb.adjust(1)
    footer = InlineKeyboardBuilder()
    footer.button(text="🔄 Refresh", callback_data=MenuCB(action="online"))
    footer.button(text="🏠 Menu", callback_data=MenuCB(action="home"))
    footer.adjust(2)
    kb.attach(footer)
    return kb.as_markup()


def inbound_filter(options: list[InboundOption]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 All clients", callback_data=PageCB(target="clients", page=0, inbound_id=-1))
    for opt in options:
        label = f"📦 {opt.remark or opt.protocol}:{opt.port}"
        kb.button(text=label, callback_data=PageCB(target="clients", page=0, inbound_id=opt.id))
    kb.adjust(1)
    kb.attach(_footer())
    return kb.as_markup()


def clients_list(
    clients: list[Client], page: int, pages: int, inbound_id: int = -1
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
    kb.attach(_footer(back_cb=MenuCB(action="clients")))
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Confirm dialogs
# ---------------------------------------------------------------------------

def confirm_delete(email: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Yes, delete", callback_data=ConfirmCB(action="yes", scope="del", arg=email))
    kb.button(text="❌ Cancel", callback_data=ClientCB(action="view", email=email))
    kb.adjust(2)
    return kb.as_markup()


def confirm_create() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Create", callback_data=ConfirmCB(action="yes", scope="create"))
    kb.button(text="❌ Cancel", callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()


def confirm_reset_all() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Yes, reset all", callback_data=ConfirmCB(action="yes", scope="reset_all")
    )
    kb.button(text="❌ Cancel", callback_data=MenuCB(action="home"))
    kb.adjust(2)
    return kb.as_markup()


# ---------------------------------------------------------------------------
# Quick-pick keyboards  (days / quota / IP-limit presets)
# ---------------------------------------------------------------------------

_DAY_PRESETS = [7, 14, 30, 90, 180, 365]


def quick_days(email: str = "", field: str = "extend") -> InlineKeyboardMarkup:
    """Preset day picker.

    field="extend"  → buttons add days; ∞ removes expiry.
    field="expiry"  → buttons set days from now; ∞ = no expiry.
    field="wiz_days" → same semantics as expiry, used in create wizard.
    """
    kb = InlineKeyboardBuilder()
    for d in _DAY_PRESETS:
        kb.button(text=f"{d}d", callback_data=QuickPickCB(field=field, value=d, email=email))
    unlimited_label = "∞ Remove expiry" if field == "extend" else "∞ No expiry"
    kb.button(text=unlimited_label, callback_data=QuickPickCB(field=field, value=0, email=email))
    kb.button(text="✏️ Custom", callback_data=QuickPickCB(field=field, value=-1, email=email))
    kb.adjust(3, 3, 2)
    back_cb = ClientCB(action="view", email=email) if email else None
    kb.attach(_footer(back_cb=back_cb))
    return kb.as_markup()


def quick_quota(email: str = "") -> InlineKeyboardMarkup:
    """Preset GB quota picker. value=0 → unlimited."""
    field = "wiz_quota" if not email else "quota"
    presets = [(0, "∞"), (1, "1 GB"), (5, "5 GB"), (10, "10 GB"),
               (20, "20 GB"), (30, "30 GB"), (50, "50 GB"), (100, "100 GB")]
    kb = InlineKeyboardBuilder()
    for val, label in presets:
        kb.button(text=label, callback_data=QuickPickCB(field=field, value=val, email=email))
    kb.button(text="✏️ Custom", callback_data=QuickPickCB(field=field, value=-1, email=email))
    kb.adjust(3, 3, 3)
    back_cb = ClientCB(action="view", email=email) if email else None
    kb.attach(_footer(back_cb=back_cb))
    return kb.as_markup()


def quick_iplimit(email: str = "") -> InlineKeyboardMarkup:
    """Preset IP-limit picker. value=0 → unlimited."""
    presets = [(0, "∞"), (1, "1"), (2, "2"), (3, "3"), (5, "5"), (10, "10")]
    kb = InlineKeyboardBuilder()
    for val, label in presets:
        kb.button(text=label, callback_data=QuickPickCB(field="iplimit", value=val, email=email))
    kb.button(text="✏️ Custom", callback_data=QuickPickCB(field="iplimit", value=-1, email=email))
    kb.adjust(3, 3, 1)
    back_cb = ClientCB(action="view", email=email) if email else None
    kb.attach(_footer(back_cb=back_cb))
    return kb.as_markup()
