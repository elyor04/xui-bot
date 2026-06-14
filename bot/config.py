"""Application configuration powered by pydantic-settings.

All values are read from environment variables or a local ``.env`` file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Telegram ----------------------------------------------------------
    bot_token: str = Field(..., description="Telegram bot token from @BotFather")
    admin_ids: Annotated[list[int], NoDecode] = Field(
        default_factory=list,
        description="Telegram user IDs that are always treated as admins",
    )

    # ---- 3x-ui panel -------------------------------------------------------
    # Base URL of the panel WITHOUT a trailing slash
    xui_base_url: str = Field(..., description="3x-ui panel base URL")
    # Web base path the panel is served under (3x-ui webBasePath). Usually "/".
    xui_base_path: str = "/"
    # Preferred: a Bearer API token (Settings -> Security -> API Token).
    xui_api_token: str | None = None
    # Fallback: username/password (cookie auth). Used only if no token is set.
    xui_username: str | None = None
    xui_password: str | None = None
    xui_verify_ssl: bool = True
    xui_timeout: int = 30

    # Public subscription base, used to render links shown to clients.
    sub_base_url: str | None = None
    # JSON subscription URL base (e.g. for clash/sing-box clients).
    json_sub_base_url: str | None = None

    # Default inbound IDs to attach when an admin creates a client and the
    # quick-create flow is used. Empty -> admin must pick during the wizard.
    default_inbound_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)

    # ---- Local database (tortoise-orm) ------------------------------------
    db_url: str = "sqlite://bot.sqlite3"

    # ---- Behaviour ---------------------------------------------------------
    # Default traffic quota (GB) and validity (days) offered in the create flow.
    default_quota_gb: int = 50
    default_days: int = 30

    # Scheduled report: send server + depleting-soon summary to all admin_ids.
    # Cron-style hours expression passed to APScheduler CronTrigger, e.g. "*/12" or "0,12"
    # fires at 00:00 and 12:00. Empty string = disabled.
    report_cron_hours: str = "*/12"

    @field_validator("admin_ids", "default_inbound_ids", mode="before")
    @classmethod
    def _split_int_list(cls, value: Any) -> Any:
        """Accept "1,2,3" strings from .env as well as real lists."""
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(part) for part in value.replace(" ", "").split(",") if part]
        return value

    @field_validator("xui_base_url")
    @classmethod
    def _strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def api_base(self) -> str:
        """Full base for /panel/api endpoints (base-path aware)."""
        base_path = "/" + self.xui_base_path.strip("/") if self.xui_base_path.strip("/") else ""
        return f"{self.xui_base_url}{base_path}".rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
