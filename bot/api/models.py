"""Pydantic models describing the slice of the 3x-ui API the bot uses.

The panel wraps every response in an envelope::

    {"success": bool, "msg": str, "obj": <payload>}

Models below describe the inner ``obj`` payloads we care about. They are kept
permissive (``extra="ignore"``) because the panel returns many more fields than
the bot reads, and the exact shape varies slightly between panel versions.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

GB = 1024 ** 3


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# --------------------------------------------------------------------------- #
# Envelope
# --------------------------------------------------------------------------- #
class ApiResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    success: bool = False
    msg: str = ""
    obj: Any = None


# --------------------------------------------------------------------------- #
# Inbounds
# --------------------------------------------------------------------------- #
class InboundOption(_Base):
    """Lightweight inbound projection from /inbounds/options."""

    id: int
    remark: str = ""
    protocol: str = ""
    port: int = 0
    tag: str = ""
    ss_method: str = Field(default="", alias="ssMethod")
    tls_flow_capable: bool = Field(default=False, alias="tlsFlowCapable")


class ClientStat(_Base):
    email: str = ""
    enable: bool = True
    up: int = 0
    down: int = 0
    total: int = 0
    expiry_time: int = Field(default=0, alias="expiryTime")
    last_online: int = Field(default=0, alias="lastOnline")  # populated in 3.3.1+

    @property
    def used(self) -> int:
        return self.up + self.down


class Inbound(_Base):
    id: int
    remark: str = ""
    protocol: str = ""
    port: int = 0
    listen: str = ""
    tag: str = ""
    enable: bool = True
    up: int = 0
    down: int = 0
    total: int = 0
    expiry_time: int = Field(default=0, alias="expiryTime")
    last_traffic_reset_time: int = Field(default=0, alias="lastTrafficResetTime")
    client_stats: list[ClientStat] = Field(default_factory=list, alias="clientStats")
    reset: int = 0


# --------------------------------------------------------------------------- #
# Clients
# --------------------------------------------------------------------------- #
class Client(_Base):
    """A panel client row (as returned by /clients/get/:email)."""

    email: str
    id: str | int | None = None      # DB row id (integer in newer panel versions)
    uuid: str | None = None          # VLESS/VMess UUID — the actual proxy identifier
    password: str | None = None      # Trojan / Shadowsocks
    flow: str | None = None
    # security = per-client auth method (e.g. Shadowsocks cipher, VLESS "none"/"reality").
    # Preserved across updates so the panel doesn't reset it.
    security: str = ""
    auth: str = ""
    group: str = ""
    enable: bool = True
    total_gb: int = Field(default=0, alias="totalGB")   # quota in BYTES (0 = unlimited)
    expiry_time: int = Field(default=0, alias="expiryTime")  # unix ms (0 = unlimited)
    last_online: int = Field(default=0, alias="lastOnline")  # unix ms of last seen
    limit_ip: int = Field(default=0, alias="limitIp")
    tg_id: str | int | None = Field(default=None, alias="tgId")
    sub_id: str | None = Field(default=None, alias="subId")
    comment: str | None = None
    reset: int = 0
    # Attached inbound ids + live traffic counters, when the endpoint enriches them.
    inbound_ids: list[int] = Field(default_factory=list, alias="inboundIds")
    up: int = 0
    down: int = 0

    @model_validator(mode="before")
    @classmethod
    def _flatten_traffic(cls, data: Any) -> Any:
        # list_clients wraps traffic counters in a nested "traffic" object;
        # always prefer it — it's the aggregated total across all inbounds.
        if isinstance(data, dict):
            traffic = data.get("traffic")
            if isinstance(traffic, dict):
                data["up"] = traffic.get("up", data.get("up", 0))
                data["down"] = traffic.get("down", data.get("down", 0))
        return data

    @property
    def used(self) -> int:
        return self.up + self.down

    @property
    def is_unlimited_traffic(self) -> bool:
        return self.total_gb == 0

    @property
    def is_unlimited_time(self) -> bool:
        return self.expiry_time == 0

    def to_update_payload(self, **overrides: Any) -> dict[str, Any]:
        """Build the writable client object accepted by /clients/update/:email.

        Only fields that belong to the client row are included (no inbound ids
        or live traffic counters). ``overrides`` patch individual fields.
        """
        # Newer panel versions return integer DB ids under "id" and the actual
        # VLESS/VMess UUID under "uuid". The panel's update endpoint expects the
        # UUID string, not the DB integer, so prefer uuid when present.
        client_id = self.uuid or (str(self.id) if self.id is not None else "")
        payload: dict[str, Any] = {
            "id": client_id,
            "password": self.password or "",
            "flow": self.flow or "",
            "security": self.security,
            "auth": self.auth,
            "group": self.group,
            "email": self.email,
            "limitIp": self.limit_ip,
            "totalGB": self.total_gb,
            "expiryTime": self.expiry_time,
            "enable": self.enable,
            "tgId": int(self.tg_id) if self.tg_id else 0,
            "subId": self.sub_id or "",
            "comment": self.comment or "",
            "reset": self.reset,
        }
        payload.update(overrides)
        return payload


class ClientCreate(_Base):
    """Builder for the client payload accepted by /clients/add.

    Admins supply human units (GB / days); ``to_payload`` converts them to the
    raw fields the panel expects and fills server-generated defaults.
    """

    email: str
    quota_gb: float = 0          # 0 -> unlimited
    days: int = 0                # 0 -> unlimited (no expiry)
    limit_ip: int = 0
    flow: str = ""
    tg_id: str | None = None
    comment: str = ""
    enable: bool = True

    def to_payload(self) -> dict[str, Any]:
        expiry_ms = 0
        if self.days > 0:
            expiry_ms = int((time.time() + self.days * 86400) * 1000)

        return {
            "id": str(uuid.uuid4()),
            "email": self.email,
            "password": "",                       # panel fills for trojan/ss
            "flow": self.flow,
            "limitIp": self.limit_ip,
            "totalGB": int(self.quota_gb * GB),
            "expiryTime": expiry_ms,
            "enable": self.enable,
            "tgId": int(self.tg_id) if self.tg_id else 0,
            "subId": uuid.uuid4().hex[:16],
            "comment": self.comment,
            "reset": 0,
        }


# --------------------------------------------------------------------------- #
# Server status
# --------------------------------------------------------------------------- #
class CpuMem(_Base):
    current: float = 0.0


class ServerStatus(_Base):
    """Subset of /server/status. The panel returns a deep nested object; we
    pull the handful of figures the bot reports and ignore the rest."""

    model_config = ConfigDict(extra="allow")

    cpu: float = 0.0
    mem: dict[str, Any] = Field(default_factory=dict)
    swap: dict[str, Any] = Field(default_factory=dict)
    disk: dict[str, Any] = Field(default_factory=dict)
    xray: dict[str, Any] = Field(default_factory=dict)
    uptime: int = 0
    loads: list[float] = Field(default_factory=list)
    tcpCount: int = 0
    udpCount: int = 0
    hostName: str = ""
    appStats: dict[str, Any] = Field(default_factory=dict)
    netIO: dict[str, Any] = Field(default_factory=dict)
    netTraffic: dict[str, Any] = Field(default_factory=dict)
    publicIP: dict[str, Any] = Field(default_factory=dict)
    ipAddresses: Any = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_loads(cls, data: Any) -> Any:
        """The API returns load as a dict {load1, load5, load15}; normalize to a list."""
        if isinstance(data, dict) and not data.get("loads"):
            load = data.get("load")
            if isinstance(load, dict):
                data["loads"] = [
                    float(load.get("load1", 0)),
                    float(load.get("load5", 0)),
                    float(load.get("load15", 0)),
                ]
        return data
