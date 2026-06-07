"""Admin menu actions: server status, online list, inbounds, backup, cleanup, and more."""
from __future__ import annotations

import time
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.api import XUIClient, XUIError
from bot.keyboards.admin import back_home, back_home_refresh, confirm_reset_all
from bot.keyboards.callbacks import ConfirmCB, MenuCB
from bot.middlewares.filters import IsAdmin
from bot.utils.formatting import LOCAL_TZ, compact_bytes, esc, fmt_expiry, fmt_expiry_card, fmt_quota, fmt_uptime_days, human_bytes

router = Router(name="admin-menu")
router.callback_query.filter(IsAdmin())

# Threshold below which a client/inbound is considered "depleting soon"
_TRAFFIC_WARN_RATIO = 0.10   # < 10 % remaining
_EXPIRY_WARN_DAYS   = 7      # < 7 days remaining


@router.callback_query(MenuCB.filter(F.action == "server"))
async def cb_server(query: CallbackQuery, api: XUIClient) -> None:
    await query.answer("Loading…")
    try:
        st = await api.server_status()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return

    online_count: int | str = "?"
    try:
        online_count = len(await api.online_clients())
    except Exception:
        pass

    mem = st.mem or {}
    xray = st.xray or {}
    loads_str = ", ".join(f"{x:.2f}" for x in st.loads[:3]) if st.loads else "—"

    xray_version = esc(str(xray.get("version", "?")))
    xray_state = esc(str(xray.get("state", "?")))

    # IP addresses — try ipAddresses list first, fall back to publicIP
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

    # Xray traffic — try xray.traffic, then netTraffic
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
    refresh_ts = datetime.now(tz=LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"📡 Xray Version: {xray_version}",
        f"🌐 IPv4: {ipv4_str}",
    ]
    if ipv6_str:
        lines.append(f"🌐 IPv6: {ipv6_str}")
    lines += [
        f"⏳ Uptime: {fmt_uptime_days(st.uptime)}",
        f"📈 System Load: {loads_str}",
        f"📋 RAM: {ram_used}/{ram_total}",
        f"🌐 Online Clients: {online_count}",
        f"🔹 TCP: {st.tcpCount}",
        f"🔸 UDP: {st.udpCount}",
        f"🚦 Traffic: {compact_bytes(xray_total)} (↑{compact_bytes(xray_up)},↓{compact_bytes(xray_down)})",
        f"ℹ️ Status: {xray_state}",
        "",
        f"📋🔄 Refreshed On: {refresh_ts}",
    ]
    await query.message.edit_text("\n".join(lines), reply_markup=back_home_refresh(MenuCB(action="server")))


@router.callback_query(MenuCB.filter(F.action == "online"))
async def cb_online(query: CallbackQuery, api: XUIClient) -> None:
    await query.answer("Loading…")
    try:
        emails = await api.online_clients()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    if not emails:
        body = "No clients are online right now."
    else:
        listed = "\n".join(f"• <code>{esc(e)}</code>" for e in emails[:60])
        more = f"\n… and {len(emails) - 60} more" if len(emails) > 60 else ""
        body = f"<b>{len(emails)}</b> online:\n{listed}{more}"
    await query.message.edit_text(
        f"🟢 <b>Online clients</b>\n\n{body}",
        reply_markup=back_home_refresh(MenuCB(action="online")),
    )


@router.callback_query(MenuCB.filter(F.action == "inbounds"))
async def cb_inbounds(query: CallbackQuery, api: XUIClient) -> None:
    await query.answer("Loading…")
    try:
        inbounds = await api.list_inbounds()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    if not inbounds:
        await query.message.edit_text("No inbounds configured.", reply_markup=back_home())
        return

    refresh_ts = datetime.now(tz=LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    sections: list[str] = []
    for ib in inbounds:
        expiry = fmt_expiry_card(ib.expiry_time, ib.reset)
        section = "\n".join([
            f"📍 Inbound: {esc(ib.remark or ib.protocol)}",
            f"🔌 Port: {ib.port}",
            f"🚦 Traffic: {compact_bytes(ib.up + ib.down)} (↑{compact_bytes(ib.up)},↓{compact_bytes(ib.down)})",
            f"👥 Clients: {len(ib.client_stats)}",
            f"📅 Expire Date: {expiry}",
        ])
        sections.append(section)

    text = "\n\n".join(sections) + f"\n\n📋🔄 Refreshed On: {refresh_ts}"
    await query.message.edit_text(text, reply_markup=back_home_refresh(MenuCB(action="inbounds")))


@router.callback_query(MenuCB.filter(F.action == "backup"))
async def cb_backup(query: CallbackQuery, api: XUIClient) -> None:
    await query.answer("Sending backup…")
    try:
        await api.backup_to_telegram()
        text = "💾 Backup dispatched to the panel's configured Telegram admins."
    except XUIError as exc:
        text = f"⚠️ {esc(str(exc))}"
    await query.message.edit_text(text, reply_markup=back_home())


@router.callback_query(MenuCB.filter(F.action == "deldepleted"))
async def cb_del_depleted(query: CallbackQuery, api: XUIClient) -> None:
    await query.answer("Cleaning up…")
    try:
        obj = await api.delete_depleted()
        count = obj.get("deleted") if isinstance(obj, dict) else obj
        text = f"🧹 Removed depleted/expired clients: <b>{esc(count)}</b>."
    except XUIError as exc:
        text = f"⚠️ {esc(str(exc))}"
    await query.message.edit_text(text, reply_markup=back_home())


@router.callback_query(MenuCB.filter(F.action == "deplete_soon"))
async def cb_deplete_soon(query: CallbackQuery, api: XUIClient) -> None:
    """Show inbounds and clients that are nearing their traffic or expiry limit."""
    await query.answer("Loading…")
    try:
        inbounds = await api.list_inbounds()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return

    now_ms = int(time.time() * 1000)
    warn_ms = _EXPIRY_WARN_DAYS * 86400 * 1000

    warn_inbounds: list[str] = []
    warn_clients: list[str] = []
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
                f"exp: {fmt_expiry(ib.expiry_time)}"
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
            if client_warn:
                exp = fmt_expiry(cs.expiry_time)
                quota = fmt_quota(cs.total)
                used = human_bytes(cs.used)
                warn_clients.append(
                    f"👤 <code>{esc(cs.email)}</code> — {used}/{quota} · exp {exp}"
                )

    lines: list[str] = [
        f"⚠️ <b>Depleting soon</b>\n",
        f"Disabled inbounds: <b>{disabled_inbounds}</b>",
        f"Disabled clients: <b>{disabled_clients}</b>\n",
    ]
    if warn_inbounds:
        lines.append("📦 <b>Inbounds near limit:</b>")
        lines.extend(warn_inbounds)
        lines.append("")
    if warn_clients:
        lines.append("👥 <b>Clients near limit:</b>")
        lines.extend(warn_clients)
    if not warn_inbounds and not warn_clients:
        lines.append("✅ No inbounds or clients are close to their limits.")

    await query.message.edit_text("\n".join(lines), reply_markup=back_home_refresh(MenuCB(action="deplete_soon")))


@router.callback_query(MenuCB.filter(F.action == "reset_all"))
async def cb_reset_all(query: CallbackQuery) -> None:
    """Prompt confirmation before resetting all client traffic counters."""
    await query.message.edit_text(
        "⚠️ <b>Reset ALL client traffic?</b>\n\n"
        "This will zero the up/down counters for every client on the panel. "
        "This action cannot be undone.",
        reply_markup=confirm_reset_all(),
    )
    await query.answer()


@router.callback_query(ConfirmCB.filter((F.action == "yes") & (F.scope == "reset_all")))
async def cb_reset_all_confirm(query: CallbackQuery, api: XUIClient) -> None:
    """Execute reset of all client traffic after confirmation."""
    await query.answer("Resetting…")
    try:
        await api.reset_all_traffics()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return
    await query.message.edit_text("✅ Traffic reset for all clients.", reply_markup=back_home())


@router.callback_query(MenuCB.filter(F.action == "sorted_report"))
async def cb_sorted_report(query: CallbackQuery, api: XUIClient) -> None:
    """Show all clients sorted by total traffic used (descending)."""
    await query.answer("Loading…")
    try:
        clients = await api.list_clients()
    except XUIError as exc:
        await query.message.edit_text(f"⚠️ {esc(str(exc))}", reply_markup=back_home())
        return

    clients_sorted = sorted(clients, key=lambda c: c.used, reverse=True)
    lines: list[str] = ["📊 <b>Clients by traffic used</b>\n"]
    for i, c in enumerate(clients_sorted[:50], 1):
        status = "🟢" if c.enable else "🔴"
        quota = fmt_quota(c.total_gb)
        exp = fmt_expiry(c.expiry_time)
        lines.append(
            f"{i}. {status} <code>{esc(c.email)}</code>\n"
            f"   {human_bytes(c.used)} / {quota} · exp {exp}"
        )
    if len(clients_sorted) > 50:
        lines.append(f"\n… and {len(clients_sorted) - 50} more clients.")
    if not clients_sorted:
        lines.append("No clients found.")
    await query.message.edit_text("\n".join(lines), reply_markup=back_home_refresh(MenuCB(action="sorted_report")))


@router.callback_query(MenuCB.filter(F.action == "commands"))
async def cb_commands(query: CallbackQuery) -> None:
    """Show available admin commands."""
    await query.answer()
    text = (
        "📋 <b>Admin commands</b>\n\n"
        "/start — open the main menu\n"
        "/find &lt;email&gt; — jump to a client by email\n"
        "/cancel — abort the current multi-step action\n\n"
        "Everything else is driven by the inline buttons."
    )
    await query.message.edit_text(text, reply_markup=back_home())


@router.callback_query(MenuCB.filter(F.action == "restart"))
async def cb_restart(query: CallbackQuery, api: XUIClient) -> None:
    """Restart the Xray service on the panel."""
    await query.answer("Restarting Xray…")
    try:
        await api.restart_xray()
        text = "⚡ Xray service restarted successfully."
    except XUIError as exc:
        text = f"⚠️ {esc(str(exc))}"
    await query.message.edit_text(text, reply_markup=back_home())
