"""Admin menu actions: server status, online list, inbounds, backup, cleanup, and more."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.api import XUIClient, XUIError
from bot.i18n import t
from bot.keyboards.admin import (
    back_home,
    back_home_refresh,
    confirm_reset_all,
    confirm_stop_xray,
    online_clients_list,
)
from bot.keyboards.callbacks import ConfirmCB, MenuCB
from bot.middlewares.filters import IsAdmin
from bot.utils.formatting import (
    compact_bytes,
    esc,
    fmt_expiry,
    fmt_expiry_card,
    fmt_quota,
    fmt_uptime_days,
    human_bytes,
    progress_bar,
)

router = Router(name="admin-menu")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

_TRAFFIC_WARN_RATIO = 0.10
_EXPIRY_WARN_DAYS   = 7


@router.callback_query(MenuCB.filter(F.action == "server"))
async def cb_server(query: CallbackQuery, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer(t("loading", lang))

    results = await asyncio.gather(
        api.server_status(),
        api.online_clients(),
        api.panel_update_info(),
        return_exceptions=True,
    )
    st_result, online_result, update_result = results

    if isinstance(st_result, BaseException):
        await query.message.edit_text(f"⚠️ {esc(str(st_result))}", reply_markup=back_home(lang))
        return

    st = st_result
    online_count: int | str = len(online_result) if isinstance(online_result, list) else "?"
    update_info: dict = update_result if isinstance(update_result, dict) else {}

    mem = st.mem or {}
    xray = st.xray or {}
    loads_str = ", ".join(f"{x:.2f}" for x in st.loads[:3]) if st.loads else "—"

    xray_version = esc(str(xray.get("version", "?")))
    xray_state = esc(str(xray.get("state", "?")))

    raw_ips = st.ipAddresses
    if isinstance(raw_ips, list):
        all_ips = [str(ip) for ip in raw_ips]
    elif isinstance(raw_ips, str) and raw_ips:
        all_ips = raw_ips.split()
    else:
        pub = st.publicIP or {}
        all_ips = [ip for ip in [pub.get("ipv4", ""), pub.get("ipv6", "")] if ip]

    ipv4_ips = [ip for ip in all_ips if ":" not in ip]
    ipv6_ips = [ip for ip in all_ips if ":" in ip]
    ipv4_str = esc(" ".join(ipv4_ips)) if ipv4_ips else "?"
    ipv6_str = esc(" ".join(ipv6_ips))

    xray_traffic = xray.get("traffic") or {}
    if isinstance(xray_traffic, dict):
        xray_up = xray_traffic.get("up", 0)
        xray_down = xray_traffic.get("down", 0)
    else:
        xray_up = xray_down = 0
    if not (xray_up or xray_down):
        net = st.netTraffic or {}
        xray_up = net.get("sent", 0)
        xray_down = net.get("recv", 0)

    xray_total = xray_up + xray_down
    ram_used = compact_bytes(mem.get("current", 0))
    ram_total = compact_bytes(mem.get("total", 0))
    refresh_ts = datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        t("server_xray_version", lang, v=xray_version),
        t("server_ipv4", lang, v=ipv4_str),
    ]
    if ipv6_str:
        lines.append(t("server_ipv6", lang, v=ipv6_str))
    lines += [
        t("server_uptime", lang, v=fmt_uptime_days(st.uptime)),
        t("server_load", lang, v=loads_str),
        t("server_ram", lang, used=ram_used, total=ram_total),
        t("server_online", lang, v=online_count),
        t("server_tcp", lang, v=st.tcpCount),
        t("server_udp", lang, v=st.udpCount),
        t("server_traffic", lang, total=compact_bytes(xray_total), up=compact_bytes(xray_up), down=compact_bytes(xray_down)),
        t("server_status_line", lang, v=xray_state),
    ]
    if update_info.get("updateAvailable"):
        latest = esc(str(update_info.get("latestVersion", "?")))
        lines.append(t("server_update_available", lang, version=latest))
    lines += ["", t("refreshed_on", lang, v=refresh_ts)]
    await query.message.edit_text("\n".join(lines), reply_markup=back_home_refresh(MenuCB(action="server"), lang))


@router.callback_query(MenuCB.filter(F.action == "online"))
async def cb_online(query: CallbackQuery, api: XUIClient, lang: str = "en") -> None:
    await query.answer(t("loading", lang))
    try:
        emails = await api.online_clients()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    if not emails:
        await query.message.edit_text(
            t("online_empty", lang),
            reply_markup=back_home_refresh(MenuCB(action="online"), lang),
        )
        return
    shown = emails[:60]
    header = t("online_title", lang, count=len(emails))
    if len(emails) > 60:
        header += t("online_showing_first", lang)
    await query.message.edit_text(header, reply_markup=online_clients_list(shown, lang))


@router.callback_query(MenuCB.filter(F.action == "inbounds"))
async def cb_inbounds(query: CallbackQuery, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer(t("loading", lang))
    try:
        inbounds = await api.list_inbounds()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    if not inbounds:
        await query.message.edit_text(t("inbounds_empty", lang), reply_markup=back_home(lang))
        return

    refresh_ts = datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")
    sections: list[str] = []
    for ib in inbounds:
        expiry = fmt_expiry_card(ib.expiry_time, ib.reset, tz)
        section = "\n".join([
            t("inbound_name", lang, v=esc(ib.remark or ib.protocol)),
            t("inbound_port", lang, v=ib.port),
            t("inbound_traffic", lang, total=compact_bytes(ib.up + ib.down), up=compact_bytes(ib.up), down=compact_bytes(ib.down)),
            t("inbound_clients", lang, v=len(ib.client_stats)),
            t("inbound_expire", lang, v=expiry),
        ])
        sections.append(section)

    text = "\n\n".join(sections) + f"\n\n{t('refreshed_on', lang, v=refresh_ts)}"
    await query.message.edit_text(text, reply_markup=back_home_refresh(MenuCB(action="inbounds"), lang))


@router.callback_query(MenuCB.filter(F.action == "backup"))
async def cb_backup(query: CallbackQuery, api: XUIClient, lang: str = "en") -> None:
    await query.answer(t("backup_sending", lang))
    try:
        await api.backup_to_telegram()
        text = t("backup_done", lang)
    except XUIError as exc:
        text = f"⚠️ {esc(str(exc))}"
    await query.message.edit_text(text, reply_markup=back_home(lang))


@router.callback_query(MenuCB.filter(F.action == "deldepleted"))
async def cb_del_depleted(query: CallbackQuery, api: XUIClient, lang: str = "en") -> None:
    await query.answer(t("cleanup_cleaning", lang))
    try:
        obj = await api.delete_depleted()
        count = obj.get("deleted") if isinstance(obj, dict) else obj
        text = t("cleanup_done", lang, count=esc(count))
    except XUIError as exc:
        text = f"⚠️ {esc(str(exc))}"
    await query.message.edit_text(text, reply_markup=back_home(lang))


@router.callback_query(MenuCB.filter(F.action == "deplete_soon"))
async def cb_deplete_soon(query: CallbackQuery, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer(t("loading", lang))
    try:
        inbounds = await api.list_inbounds()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return

    now_ms = int(time.time() * 1000)
    warn_ms = _EXPIRY_WARN_DAYS * 86400 * 1000

    warn_inbounds: list[str] = []
    warn_clients: list[str] = []
    seen_client_emails: set[str] = set()
    disabled_inbounds = 0
    disabled_clients = 0

    for ib in inbounds:
        if not ib.enable:
            disabled_inbounds += 1
            continue
        ib_warn = False
        if ib.total > 0:
            remaining = ib.total - (ib.up + ib.down)
            if remaining < ib.total * _TRAFFIC_WARN_RATIO:
                ib_warn = True
        if ib.expiry_time > 0 and (ib.expiry_time - now_ms) < warn_ms:
            ib_warn = True
        if ib_warn:
            warn_inbounds.append(
                f"📦 <b>{esc(ib.remark or ib.protocol)}</b> #{ib.id} — "
                f"traffic left: {human_bytes(max(0, ib.total - ib.up - ib.down))} · "
                f"exp: {fmt_expiry(ib.expiry_time, tz)}"
            )

        for cs in ib.client_stats:
            if not cs.enable:
                disabled_clients += 1
                continue
            client_warn = False
            if cs.total > 0:
                remaining = cs.total - cs.used
                if remaining < cs.total * _TRAFFIC_WARN_RATIO:
                    client_warn = True
            if cs.expiry_time > 0 and (cs.expiry_time - now_ms) < warn_ms:
                client_warn = True
            if client_warn and cs.email not in seen_client_emails:
                seen_client_emails.add(cs.email)
                exp = fmt_expiry(cs.expiry_time, tz)
                quota = fmt_quota(cs.total)
                used = human_bytes(cs.used)
                bar = f" {progress_bar(cs.used, cs.total, 8)}" if cs.total else ""
                last_seen = ""
                if cs.last_online > 0:
                    try:
                        from datetime import datetime as _dt
                        last_seen = f" · seen {_dt.fromtimestamp(cs.last_online / 1000, tz=tz):%Y-%m-%d}"
                    except Exception:
                        pass
                warn_clients.append(
                    f"👤 <code>{esc(cs.email)}</code> — {used}/{quota}{bar} · exp {exp}{last_seen}"
                )

    lines: list[str] = [
        t("deplete_title", lang),
        t("deplete_disabled_inbounds", lang, v=disabled_inbounds),
        t("deplete_disabled_clients", lang, v=disabled_clients) + "\n",
    ]
    if warn_inbounds:
        lines.append(t("deplete_inbounds_header", lang))
        lines.extend(warn_inbounds)
        lines.append("")
    if warn_clients:
        lines.append(t("deplete_clients_header", lang))
        lines.extend(warn_clients)
    if not warn_inbounds and not warn_clients:
        lines.append(t("deplete_none", lang))

    await query.message.edit_text("\n".join(lines), reply_markup=back_home_refresh(MenuCB(action="deplete_soon"), lang))


@router.callback_query(MenuCB.filter(F.action == "reset_all"))
async def cb_reset_all(query: CallbackQuery, lang: str = "en") -> None:
    await query.message.edit_text(
        t("reset_all_confirm", lang),
        reply_markup=confirm_reset_all(lang),
    )
    await query.answer()


@router.callback_query(ConfirmCB.filter((F.action == "yes") & (F.scope == "reset_all")))
async def cb_reset_all_confirm(query: CallbackQuery, api: XUIClient, lang: str = "en") -> None:
    await query.answer(t("reset_all_resetting", lang))
    try:
        await api.reset_all_traffics()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return
    await query.message.edit_text(t("reset_all_done", lang), reply_markup=back_home(lang))


@router.callback_query(MenuCB.filter(F.action == "sorted_report"))
async def cb_sorted_report(query: CallbackQuery, api: XUIClient, lang: str = "en", tz: ZoneInfo | None = None) -> None:
    await query.answer(t("loading", lang))
    try:
        clients = await api.list_clients()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home(lang))
        return

    clients_sorted = sorted(clients, key=lambda c: c.used, reverse=True)
    lines: list[str] = [t("sorted_title", lang)]
    for i, c in enumerate(clients_sorted[:50], 1):
        status = "🟢" if c.enable else "🔴"
        quota = fmt_quota(c.total_gb)
        exp = fmt_expiry(c.expiry_time, tz)
        bar = f" {progress_bar(c.used, c.total_gb, 8)}" if c.total_gb else ""
        lines.append(
            f"{i}. {status} <code>{esc(c.email)}</code>\n"
            f"   {human_bytes(c.used)} / {quota}{bar} · exp {exp}"
        )
    if len(clients_sorted) > 50:
        lines.append(t("sorted_more", lang, count=len(clients_sorted) - 50))
    if not clients_sorted:
        lines.append(t("sorted_empty", lang))
    await query.message.edit_text("\n".join(lines), reply_markup=back_home_refresh(MenuCB(action="sorted_report"), lang))


@router.callback_query(MenuCB.filter(F.action == "commands"))
async def cb_commands(query: CallbackQuery, lang: str = "en") -> None:
    await query.answer()
    await query.message.edit_text(t("commands_text", lang), reply_markup=back_home(lang))


@router.callback_query(MenuCB.filter(F.action == "restart"))
async def cb_restart(query: CallbackQuery, api: XUIClient, lang: str = "en") -> None:
    await query.answer(t("restart_restarting", lang))
    try:
        await api.restart_xray()
        text = t("restart_done", lang)
    except XUIError as exc:
        text = f"⚠️ {esc(str(exc))}"
    await query.message.edit_text(text, reply_markup=back_home(lang))


@router.callback_query(MenuCB.filter(F.action == "stop_xray"))
async def cb_stop_xray(query: CallbackQuery, lang: str = "en") -> None:
    await query.message.edit_text(t("stop_xray_confirm", lang), reply_markup=confirm_stop_xray(lang))
    await query.answer()


@router.callback_query(ConfirmCB.filter((F.action == "yes") & (F.scope == "stop_xray")))
async def cb_stop_xray_confirm(query: CallbackQuery, api: XUIClient, lang: str = "en") -> None:
    await query.answer(t("stop_xray_stopping", lang))
    try:
        await api.stop_xray()
        text = t("stop_xray_stopped", lang)
    except XUIError as exc:
        text = f"⚠️ {esc(str(exc))}"
    await query.message.edit_text(text, reply_markup=back_home(lang))


@router.message(Command("restart"))
async def cmd_restart(message: Message, api: XUIClient, lang: str = "en") -> None:
    try:
        await api.restart_xray()
        await message.answer(t("restart_done", lang))
    except XUIError as exc:
        await message.answer(f"⚠️ {esc(str(exc))}")


@router.callback_query(MenuCB.filter(F.action == "logs"))
async def cb_logs(query: CallbackQuery, api: XUIClient, lang: str = "en") -> None:
    await query.answer(t("loading", lang))
    logs = await api.xray_logs(50)
    if not logs:
        await query.message.edit_text(t("logs_empty", lang), reply_markup=back_home(lang))
        return
    header = t("logs_title", lang, count=len(logs))
    body = "\n".join(logs)
    text = f"{header}\n\n<code>{esc(body)}</code>"
    if len(text) > 4000:
        text = text[:4000] + "…</code>"
    await query.message.edit_text(text, reply_markup=back_home_refresh(MenuCB(action="logs"), lang))


@router.message(Command("logs"))
async def cmd_logs(message: Message, api: XUIClient, lang: str = "en") -> None:
    args = (message.text or "").split(maxsplit=1)
    count = 50
    if len(args) > 1:
        try:
            count = max(1, min(int(args[1].strip()), 200))
        except ValueError:
            pass
    logs = await api.xray_logs(count)
    if not logs:
        await message.answer(t("logs_empty", lang))
        return
    header = t("logs_title", lang, count=len(logs))
    body = "\n".join(logs)
    text = f"{header}\n\n<code>{esc(body)}</code>"
    if len(text) > 4000:
        text = text[:4000] + "…</code>"
    await message.answer(text)
