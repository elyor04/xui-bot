"""Small presentation helpers (bytes, dates, durations)."""
from __future__ import annotations

import html
import io
import json
import time
import qrcode
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

GB = 1024 ** 3
LOCAL_TZ = datetime.now().astimezone().tzinfo


def get_tz(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, KeyError):
        return ZoneInfo("UTC")


def make_qr_png(data: str) -> bytes:
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def human_bytes(n: int | float) -> str:
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < 1024.0:
            return f"{n:.2f} {unit}" if unit != "B" else f"{int(n)} {unit}"
        n /= 1024.0
    return f"{n:.2f} EB"


def fmt_quota(total_bytes: int) -> str:
    return "∞" if not total_bytes else human_bytes(total_bytes)


def fmt_expiry(expiry_ms: int, tz: ZoneInfo | None = None) -> str:
    """Render a panel expiryTime (unix ms) as a friendly string.

    A value of 0 means unlimited. Negative values are interpreted as a
    'days from first use' duration, which 3x-ui uses for unused clients.
    """
    if not expiry_ms:
        return "∞ (no expiry)"
    if expiry_ms < 0:
        days = abs(expiry_ms) // (1000 * 86400)
        return f"{days} days from first use"
    dt = datetime.fromtimestamp(expiry_ms / 1000, tz=tz or LOCAL_TZ)
    remaining = expiry_ms / 1000 - time.time()
    if remaining <= 0:
        return f"{dt:%Y-%m-%d} (expired)"
    days = int(remaining // 86400)
    return f"{dt:%Y-%m-%d} ({days}d left)"


def fmt_uptime(seconds: int) -> str:
    seconds = int(seconds or 0)
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if h:
        parts.append(f"{h}h")
    parts.append(f"{m}m")
    return " ".join(parts)


def progress_bar(used: int, total: int, width: int = 12) -> str:
    if not total:
        return "—"
    ratio = min(used / total, 1.0)
    filled = int(ratio * width)
    return "█" * filled + "░" * (width - filled) + f" {ratio * 100:.0f}%"


def esc(text: str | None) -> str:
    return html.escape(str(text)) if text is not None else ""


def compact_bytes(n: int | float) -> str:
    """Like human_bytes but no space between number and unit."""
    n = float(n or 0)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(n) < 1024.0:
            return f"{n:.2f}{unit}"
        n /= 1024.0
    return f"{n:.2f}EB"


def fmt_expiry_card(expiry_ms: int, reset: int = 0, tz: ZoneInfo | None = None) -> str:
    """Render expiry in the new card style."""
    suffix = "(Reset)" if reset else ""
    if not expiry_ms:
        return f"♾️ Unlimited{suffix}"
    if expiry_ms < 0:
        days = abs(expiry_ms) // (1000 * 86400)
        return f"{days}d from first use{suffix}"
    dt = datetime.fromtimestamp(expiry_ms / 1000, tz=tz or LOCAL_TZ)
    remaining = expiry_ms / 1000 - time.time()
    if remaining <= 0:
        return f"{dt:%Y-%m-%d} (expired){suffix}"
    days = int(remaining // 86400)
    return f"{dt:%Y-%m-%d} ({days}d left){suffix}"


def fmt_quota_card(total_bytes: int, reset: int = 0) -> str:
    """Render quota in the new card style."""
    suffix = "(Reset)" if reset else ""
    if not total_bytes:
        return f"♾️ Unlimited{suffix}"
    return compact_bytes(total_bytes)


def fmt_uptime_days(seconds: int) -> str:
    return f"{int(seconds or 0) // 86400} Days"


def extract_last_online(raw: object, tz: ZoneInfo | None = None) -> str | None:
    """Extract the most recent timestamp from a client IP log."""
    if raw is None:
        return None
    if isinstance(raw, str):
        raw_str = raw.strip()
        if not raw_str:
            return None
        try:
            raw = json.loads(raw_str)
        except json.JSONDecodeError:
            return None
    if not isinstance(raw, list) or not raw:
        return None
    latest_ts: int | None = None
    for entry in raw:
        if isinstance(entry, dict):
            ts = entry.get("timestamp") or entry.get("time")
            if ts:
                try:
                    ts_int = int(ts)
                    if latest_ts is None or ts_int > latest_ts:
                        latest_ts = ts_int
                except (ValueError, TypeError):
                    pass
    if latest_ts is None:
        return None
    try:
        dt = datetime.fromtimestamp(latest_ts, tz=tz or LOCAL_TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return None


def fmt_ips(raw: object, tz: ZoneInfo | None = None) -> str:
    """Render an IP log from the panel into a readable string.

    Panel sends either:
      • a list of strings:              ["1.2.3.4", "5.6.7.8"]
      • a list of dicts with timestamp: [{"ip": "1.2.3.4", "timestamp": 1710000000}]
      • a JSON string of the above
      • None / empty → "No IPs logged."
    """
    if raw is None:
        return "No IPs logged."

    # If the panel returned a JSON string, decode it first.
    if isinstance(raw, str):
        raw_str = raw.strip()
        if not raw_str:
            return "No IPs logged."
        try:
            raw = json.loads(raw_str)
        except json.JSONDecodeError:
            return esc(raw_str)

    if not isinstance(raw, list) or not raw:
        return "No IPs logged."

    lines: list[str] = []
    for entry in raw:
        if isinstance(entry, dict):
            ip = entry.get("ip") or entry.get("address") or "?"
            ts = entry.get("timestamp") or entry.get("time")
            if ts:
                try:
                    dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                    lines.append(f"<code>{esc(ip)}</code>  {dt.astimezone(tz or LOCAL_TZ):%Y-%m-%d %H:%M}")
                except (ValueError, OSError):
                    lines.append(f"<code>{esc(ip)}</code>")
            else:
                lines.append(f"<code>{esc(ip)}</code>")
        else:
            lines.append(f"<code>{esc(str(entry))}</code>")

    return "\n".join(lines) if lines else "No IPs logged."
