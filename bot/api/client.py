"""Async client for the 3x-ui panel API, built on aiohttp.

Authentication:
  * If ``xui_api_token`` is set, every request carries an
    ``Authorization: Bearer <token>`` header (CSRF is short-circuited for
    token callers, per the panel docs).
  * Otherwise the client logs in with username/password, keeps the session
    cookie in aiohttp's cookie jar, and re-logs in once on auth failure.

Every panel reply is the ``{success, msg, obj}`` envelope; :meth:`_request`
unwraps it and raises :class:`XUIRequestError` when ``success`` is false.
"""
from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any

import aiohttp

from bot.api.exceptions import XUIAuthError, XUIError, XUIRequestError
from bot.api.models import (
    ApiResponse,
    Client,
    Inbound,
    InboundOption,
    ServerStatus,
)
from bot.config import Settings

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF = 1.0  # seconds; doubled each attempt (1s, 2s)


class XUIClient:
    def __init__(self, settings: Settings) -> None:
        self._s = settings
        self._session: aiohttp.ClientSession | None = None
        self._authed = False

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def start(self) -> None:
        if self._session and not self._session.closed:
            return
        connector = None
        if self._s.xui_base_url.startswith("https") and not self._s.xui_verify_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ctx)
        headers = {"Accept": "application/json"}
        if self._s.xui_api_token:
            headers["Authorization"] = f"Bearer {self._s.xui_api_token}"
            self._authed = True
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self._s.xui_timeout),
            connector=connector,
            headers=headers,
        )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "XUIClient":
        await self.start()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------ #
    # Auth (cookie mode)
    # ------------------------------------------------------------------ #
    async def login(self) -> None:
        if self._s.xui_api_token:
            self._authed = True
            return
        if not (self._s.xui_username and self._s.xui_password):
            raise XUIAuthError("No API token and no username/password configured.")
        assert self._session is not None
        url = f"{self._s.api_base}/login"
        async with self._session.post(
            url, json={"username": self._s.xui_username, "password": self._s.xui_password}
        ) as resp:
            data = await _safe_json(resp)
            env = ApiResponse(**data) if isinstance(data, dict) else ApiResponse()
            if not env.success:
                raise XUIAuthError(env.msg or "Login failed")
        self._authed = True

    # ------------------------------------------------------------------ #
    # Core request
    # ------------------------------------------------------------------ #
    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        raw: bool = False,
        _retry: bool = True,
    ) -> Any:
        if self._session is None:
            await self.start()
        if not self._authed:
            await self.login()

        url = f"{self._s.api_base}{path}"
        assert self._session is not None

        last_exc: Exception | None = None
        for attempt in range(_RETRY_ATTEMPTS):
            if attempt:
                delay = _RETRY_BACKOFF * (2 ** (attempt - 1))
                logger.warning(
                    "Retrying %s %s (attempt %d/%d) in %.1fs…",
                    method, path, attempt + 1, _RETRY_ATTEMPTS, delay,
                )
                await asyncio.sleep(delay)
            try:
                async with self._session.request(
                    method, url, json=json, data=data, params=params
                ) as resp:
                    if resp.status in (401, 403) and _retry and not self._s.xui_api_token:
                        # Cookie likely expired → log in again and retry once.
                        self._authed = False
                        await self.login()
                        return await self._request(
                            method, path, json=json, data=data, params=params, raw=raw, _retry=False
                        )
                    if resp.status in (401, 403):
                        raise XUIAuthError(f"Unauthorized ({resp.status}) for {path}")
                    if raw:
                        if resp.status >= 400:
                            raise XUIRequestError(f"HTTP {resp.status} for {path}", status=resp.status)
                        return await resp.read()
                    payload = await _safe_json(resp)
                    if resp.status >= 400:
                        msg = payload.get("msg") if isinstance(payload, dict) else str(payload)
                        raise XUIRequestError(msg or f"HTTP {resp.status}", status=resp.status)
                    env = ApiResponse(**payload) if isinstance(payload, dict) else ApiResponse(obj=payload)
                    if not env.success:
                        raise XUIRequestError(env.msg or f"Panel returned success=false (obj={env.obj!r})")
                    return env.obj
            except XUIAuthError:
                raise  # never retry auth failures
            except XUIRequestError as exc:
                if exc.status is None or exc.status < 500:
                    raise  # 4xx and panel-level errors are not transient
                last_exc = exc
            except aiohttp.ClientError as exc:
                last_exc = exc

        raise last_exc  # type: ignore[misc]

    # ================================================================== #
    # Inbounds
    # ================================================================== #
    async def list_inbounds(self) -> list[Inbound]:
        obj = await self._request("GET", "/panel/api/inbounds/list")
        return [Inbound(**i) for i in (obj or [])]

    async def inbound_options(self) -> list[InboundOption]:
        obj = await self._request("GET", "/panel/api/inbounds/options")
        return [InboundOption(**i) for i in (obj or [])]

    async def get_inbound(self, inbound_id: int) -> Inbound:
        obj = await self._request("GET", f"/panel/api/inbounds/get/{inbound_id}")
        return Inbound(**obj)

    async def set_inbound_enable(self, inbound_id: int, enable: bool) -> None:
        await self._request(
            "POST", f"/panel/api/inbounds/setEnable/{inbound_id}", json={"enable": enable}
        )

    # ================================================================== #
    # Clients
    # ================================================================== #
    async def list_clients(self) -> list[Client]:
        obj = await self._request("GET", "/panel/api/clients/list")
        return [Client(**c) for c in (obj or [])]

    async def search_clients(
        self,
        search: str,
        *,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[Client], int]:
        """GET /panel/api/clients/list/paged — case-insensitive substring match on email/subId/comment.

        Returns (clients, filtered_count) where filtered_count is the total number of
        matching rows across all pages (not just the current page).
        """
        params: dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
            "search": search,
            "filter": "",
            "protocol": "",
            "sort": "",
            "order": "",
        }
        obj = await self._request("GET", "/panel/api/clients/list/paged", params=params)
        if not isinstance(obj, dict):
            return [], 0
        raw_items: list[dict] = obj.get("items") or []
        clients = [Client(**item) for item in raw_items]
        filtered: int = obj.get("filtered", len(clients))
        return clients, filtered

    async def get_clients_by_tgid(self, tg_id: int) -> list[Client]:
        """Return all panel clients whose tgId matches ``tg_id``."""
        clients = await self.list_clients()
        matched = []
        for c in clients:
            try:
                if c.tg_id and int(c.tg_id) == tg_id:
                    matched.append(c)
            except (ValueError, TypeError):
                continue
        return matched

    async def get_client(self, email: str) -> Client | None:
        try:
            obj = await self._request("GET", f"/panel/api/clients/get/{email}")
        except XUIRequestError:
            return None
        if not obj:
            return None
        if isinstance(obj, dict) and "client" in obj:
            flat: dict[str, Any] = {**obj["client"], "inboundIds": obj.get("inboundIds") or []}
        elif isinstance(obj, dict):
            flat = dict(obj)
        else:
            return None

        # Enrich with aggregated traffic counters + lastOnline from the
        # traffic endpoint (up/down/lastOnline across all inbounds).
        try:
            traffic = await self.client_traffic(email)
            if traffic:
                flat["up"] = traffic.get("up") or 0
                flat["down"] = traffic.get("down") or 0
                flat["lastOnline"] = traffic.get("lastOnline") or 0
        except Exception:
            pass

        return Client(**flat)

    async def client_traffic(self, email: str) -> dict[str, Any] | None:
        """GET /panel/api/clients/traffic/:email — aggregated traffic for one client."""
        try:
            obj = await self._request("GET", f"/panel/api/clients/traffic/{email}")
        except XUIRequestError:
            return None
        return obj if isinstance(obj, dict) else None

    async def add_client(self, payload: dict[str, Any], inbound_ids: list[int]) -> Any:
        body = {"client": payload, "inboundIds": inbound_ids}
        return await self._request("POST", "/panel/api/clients/add", json=body)

    async def update_client(self, email: str, payload: dict[str, Any]) -> Any:
        return await self._request("POST", f"/panel/api/clients/update/{email}", json=payload)

    async def delete_client(self, email: str, keep_traffic: bool = False) -> Any:
        params = {"keepTraffic": "1"} if keep_traffic else None
        return await self._request(
            "POST", f"/panel/api/clients/del/{email}", params=params
        )

    async def reset_client_traffic(self, email: str) -> Any:
        return await self._request("POST", f"/panel/api/clients/resetTraffic/{email}")

    async def bulk_adjust(
        self, emails: list[str], add_days: int = 0, add_bytes: int = 0
    ) -> Any:
        body = {"emails": emails, "addDays": add_days, "addBytes": add_bytes}
        return await self._request("POST", "/panel/api/clients/bulkAdjust", json=body)

    async def extend_client(self, email: str, add_days: int = 0, add_gb: float = 0) -> Any:
        return await self.bulk_adjust(
            [email], add_days=add_days, add_bytes=int(add_gb * (1024 ** 3))
        )

    async def client_links(self, email: str) -> list[str]:
        obj = await self._request("GET", f"/panel/api/clients/links/{email}")
        return list(obj or [])

    async def sub_links(self, sub_id: str) -> list[str]:
        obj = await self._request("GET", f"/panel/api/clients/subLinks/{sub_id}")
        return list(obj or [])

    async def client_ips(self, email: str) -> Any:
        return await self._request("POST", f"/panel/api/clients/ips/{email}")

    async def clear_client_ips(self, email: str) -> Any:
        return await self._request("POST", f"/panel/api/clients/clearIps/{email}")

    async def online_clients(self) -> list[str]:
        obj = await self._request("POST", "/panel/api/clients/onlines")
        return list(obj or [])

    async def delete_depleted(self) -> Any:
        return await self._request("POST", "/panel/api/clients/delDepleted")

    async def reset_all_traffics(self) -> Any:
        return await self._request("POST", "/panel/api/clients/resetAllTraffics")

    async def bulk_delete_clients(self, emails: list[str]) -> Any:
        """DELETE /panel/api/clients/bulkDel — remove multiple clients at once."""
        return await self._request("POST", "/panel/api/clients/bulkDel", json={"emails": emails})

    async def bulk_reset_traffic(self, emails: list[str]) -> Any:
        """POST /panel/api/clients/bulkResetTraffic — reset traffic for multiple clients."""
        return await self._request("POST", "/panel/api/clients/bulkResetTraffic", json={"emails": emails})

    async def attach_client_to_inbound(self, email: str, inbound_id: int) -> Any:
        """POST /panel/api/clients/:email/attach — attach client to an additional inbound."""
        return await self._request("POST", f"/panel/api/clients/{email}/attach", json={"inboundId": inbound_id})

    async def detach_client_from_inbound(self, email: str, inbound_id: int) -> Any:
        """POST /panel/api/clients/:email/detach — detach client from an inbound."""
        return await self._request("POST", f"/panel/api/clients/{email}/detach", json={"inboundId": inbound_id})

    async def delete_all_inbound_clients(self, inbound_id: int) -> Any:
        """POST /panel/api/inbounds/:id/delAllClients — wipe every client from an inbound."""
        return await self._request("POST", f"/panel/api/inbounds/{inbound_id}/delAllClients")

    # ================================================================== #
    # Server
    # ================================================================== #
    async def server_status(self) -> ServerStatus:
        obj = await self._request("GET", "/panel/api/server/status")
        return ServerStatus(**(obj or {}))

    async def new_uuid(self) -> str:
        obj = await self._request("GET", "/panel/api/server/getNewUUID")
        if isinstance(obj, dict):
            return obj.get("uuid") or obj.get("id") or ""
        return str(obj)

    async def restart_xray(self) -> Any:
        return await self._request("POST", "/panel/api/server/restartXrayService")

    async def backup_to_telegram(self) -> Any:
        return await self._request("POST", "/panel/api/backuptotgbot")


async def _safe_json(resp: aiohttp.ClientResponse) -> Any:
    try:
        return await resp.json(content_type=None)
    except Exception as exc:  # noqa: BLE001
        text = await resp.text()
        raise XUIError(f"Non-JSON response ({resp.status}): {text[:200]}") from exc
