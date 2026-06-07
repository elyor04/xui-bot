"""Shared handlers: /start, /help, /cancel, home-menu dispatcher, language selection."""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    ErrorEvent,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

logger = logging.getLogger(__name__)

from bot.api import XUIClient
from bot.db.models import Role, User
from bot.i18n import t
from bot.keyboards.admin import admin_menu
from bot.keyboards.callbacks import LangCB, MenuCB, PickModeCB
from bot.keyboards.client import client_menu, language_picker, mode_picker, pick_client, timezone_kb
from bot.states import FindClient, SelectTimezone
from bot.utils.formatting import compact_bytes, esc, fmt_expiry_card

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


# ---------------------------------------------------------------------------
# Timezone selection
# ---------------------------------------------------------------------------
_POPULAR_TZ = [
    "UTC", "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Moscow",
    "Asia/Tashkent", "Asia/Tehran", "Asia/Dubai", "Asia/Kolkata",
    "Asia/Dhaka", "Asia/Bangkok", "Asia/Shanghai", "Asia/Tokyo",
    "Africa/Cairo", "America/New_York", "America/Chicago",
    "America/Denver", "America/Los_Angeles", "America/Sao_Paulo",
    "Australia/Sydney",
]


@router.message(Command("timezone"))
async def cmd_timezone(message: Message, user: User, state: FSMContext, lang: str = "en") -> None:
    await state.set_state(SelectTimezone.waiting)
    await message.answer(
        t("tz_title", lang, tz=esc(user.timezone or "UTC")),
        reply_markup=timezone_kb(lang),
    )


@router.inline_query()
async def handle_inline_query(
    query: InlineQuery,
    user: User,
    state: FSMContext,
    api: XUIClient,
    lang: str = "en",
    tz: ZoneInfo | None = None,
) -> None:
    q = query.query.strip()
    current_state = await state.get_state()

    if current_state == FindClient.email.state and user.is_admin:
        await _inline_find_clients(query, api, q, lang, tz)
    else:
        await _inline_timezones(query, q, lang)


async def _inline_find_clients(
    query: InlineQuery,
    api: XUIClient,
    q: str,
    lang: str,
    tz: ZoneInfo | None,
) -> None:
    if not q:
        await query.answer([], cache_time=5, is_personal=True)
        return
    try:
        result = await api.search_clients(q, page_size=50)
    except Exception:
        await query.answer([], cache_time=5, is_personal=True)
        return

    items: list[dict] = result.get("items") or []
    results: list[InlineQueryResultArticle] = []
    for item in items[:50]:
        email = item.get("email", "")
        if not email:
            continue
        up = item.get("up", 0) or 0
        down = item.get("down", 0) or 0
        total_gb = item.get("totalGB", 0) or 0
        expiry_ms = item.get("expiryTime", 0) or 0
        used_str = compact_bytes(up + down)
        quota_str = "∞" if not total_gb else compact_bytes(total_gb)
        exp_str = fmt_expiry_card(expiry_ms, tz=tz)
        results.append(
            InlineQueryResultArticle(
                id=email,
                title=email,
                description=f"{used_str} / {quota_str} · {exp_str}",
                input_message_content=InputTextMessageContent(message_text=email),
            )
        )
    await query.answer(results, cache_time=10, is_personal=True)


async def _inline_timezones(query: InlineQuery, q: str, lang: str) -> None:
    search = q.lower()
    from zoneinfo import available_timezones
    all_tzs = sorted(available_timezones())

    if search:
        def _rank(name: str) -> int:
            lo = name.lower()
            city = lo.split("/")[-1]
            if lo == search:
                return 0
            if city == search:
                return 1
            if city.startswith(search):
                return 2
            if lo.startswith(search):
                return 3
            return 4

        candidates = [tz for tz in all_tzs if search in tz.lower()]
        candidates.sort(key=_rank)
    else:
        candidates = [tz for tz in _POPULAR_TZ if tz in all_tzs]

    results: list[InlineQueryResultArticle] = []
    for tz_name in candidates[:50]:
        try:
            tz_obj = ZoneInfo(tz_name)
            now = datetime.now(tz=tz_obj)
            offset = now.utcoffset()
            total_secs = int(offset.total_seconds())
            sign = "+" if total_secs >= 0 else "-"
            h, rem = divmod(abs(total_secs), 3600)
            m = rem // 60
            offset_str = f"UTC{sign}{h:02d}:{m:02d}"
            results.append(
                InlineQueryResultArticle(
                    id=tz_name,
                    title=tz_name,
                    description=f"{offset_str} · now {now:%H:%M}",
                    input_message_content=InputTextMessageContent(message_text=tz_name),
                )
            )
        except Exception:
            continue

    await query.answer(results, cache_time=60, is_personal=True)


@router.message(SelectTimezone.waiting)
async def tz_set_message(message: Message, user: User, state: FSMContext, lang: str = "en") -> None:
    tz_name = (message.text or "").strip()
    try:
        ZoneInfo(tz_name)
        user.timezone = tz_name
        await user.save()
        await state.clear()
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(t("tz_set", lang, tz=esc(tz_name)), reply_markup=home_markup(user, lang))
    except (ZoneInfoNotFoundError, KeyError):
        await message.answer(t("tz_invalid", lang), reply_markup=timezone_kb(lang))


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
