"""Typed callback data factories (aiogram CallbackData)."""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="menu"):
    action: str  # e.g. "clients", "server", "create", "online", "backup", "home"


class ClientCB(CallbackData, prefix="cl"):
    action: str  # "view", "reset", "extend", "del", "links", "ips", "toggle", "clearips"
    email: str


class InbPickCB(CallbackData, prefix="inb"):
    action: str  # "toggle", "done"
    inbound_id: int = 0


class PageCB(CallbackData, prefix="pg"):
    target: str  # "clients"
    page: int
    inbound_id: int = -1  # -1 = no filter (all clients)


class ConfirmCB(CallbackData, prefix="cfm"):
    action: str  # "yes" / "no"
    scope: str   # "create" / "del"
    arg: str = ""


class PickClientCB(CallbackData, prefix="pkcl"):
    email: str


class PickModeCB(CallbackData, prefix="mode"):
    action: str   # "admin" | "client" | "switch"
    email: str = ""


class QuickPickCB(CallbackData, prefix="qp"):
    """Preset-value picker for days / GB / IP-limit fields.

    value:  ≥ 0 = the chosen preset; -1 = "Custom" (fall back to text input).
    email:  client email for per-client flows; "" for create-wizard flows.
    field:  "extend" | "quota" | "expiry" | "iplimit" | "wiz_quota" | "wiz_days"
    """

    field: str
    value: int
    email: str = ""


class LangCB(CallbackData, prefix="lang"):
    code: str  # "en" | "uz" | "ru" | "zh" | "fa"


class NumpadCB(CallbackData, prefix="np"):
    """Inline numpad for entering custom numbers (quota GB, days, IP count).

    digit: 0-9 = append digit; -1 = backspace; -2 = reset/show; 100 = confirm
    """

    field: str   # "quota" | "extend" | "expiry" | "iplimit"
    email: str
    val: int     # current accumulated value (0..999999)
    digit: int   # -2=reset, -1=backspace, 0-9=digit, 100=confirm
