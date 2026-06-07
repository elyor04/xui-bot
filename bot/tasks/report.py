from __future__ import annotations

import logging
import time

from aiogram import Bot

from bot.api import XUIClient, XUIError
from bot.config import Settings
from bot.db.models import User
from bot.i18n import DEFAULT_LANG, t
from bot.utils.formatting import fmt_uptime, human_bytes

logger = logging.getLogger("xui_bot.tasks.report")

_DEPLETE_THRESHOLD_DAYS = 7
_DEPLETE_TRAFFIC_RATIO  = 0.85


def _build_report(status, clients, online, lang: str) -> str:
    now_ms = int(time.time() * 1000)
    threshold_ms = now_ms + _DEPLETE_THRESHOLD_DAYS * 86400 * 1000

    depleting: list[str] = []
    for c in clients:
        if not c.enable:
            continue
        if 0 < c.expiry_time <= threshold_ms:
            depleting.append(c.email)
            continue
        if c.total_gb and c.used >= _DEPLETE_TRAFFIC_RATIO * c.total_gb:
            depleting.append(c.email)

    mem_d  = status.mem  or {}
    disk_d = status.disk or {}
    xray_d = status.xray or {}
    xray_state = xray_d.get("state", "?")

    def _pct(d: dict) -> str:
        cur, tot = d.get("current", 0), d.get("total", 0)
        if tot:
            return f"{cur / tot * 100:.0f}%  ({human_bytes(cur)}/{human_bytes(tot)})"
        return human_bytes(cur)

    parts: list[str] = [
        t("report_title", lang),
        "",
        t("report_cpu", lang, v=f"{status.cpu:.1f}"),
        t("report_ram", lang, v=_pct(mem_d)),
        t("report_disk", lang, v=_pct(disk_d)),
        t("report_uptime", lang, uptime=fmt_uptime(status.uptime), xray=xray_state),
        t("report_stats", lang, total=len(clients), online=len(online)),
    ]

    if depleting:
        parts.append("")
        parts.append(t("report_depleting", lang, count=len(depleting)))
        for email in depleting[:20]:
            parts.append(f"  • {email}")
        if len(depleting) > 20:
            parts.append(t("report_and_more", lang, count=len(depleting) - 20))

    return "\n".join(parts)


async def send_report(bot: Bot, api: XUIClient, settings: Settings) -> None:
    try:
        status  = await api.server_status()
        clients = await api.list_clients()
        online  = await api.online_clients()
    except XUIError as exc:
        logger.warning("Report fetch error: %s", exc)
        return

    for uid in settings.admin_ids:
        try:
            db_user = await User.get_or_none(tg_id=uid)
            lang = db_user.language if db_user else DEFAULT_LANG
            text = _build_report(status, clients, online, lang)
            await bot.send_message(uid, text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not send report to %s: %s", uid, exc)
