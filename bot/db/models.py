"""Local persistence (tortoise-orm).

The bot keeps a small local table mapping Telegram users to roles and, for
clients, to their panel ``email``. The panel itself remains the source of
truth for VPN accounts; this table only records who-is-who for the bot.
"""
from __future__ import annotations

from enum import StrEnum

from tortoise import fields
from tortoise.models import Model


class Role(StrEnum):
    ADMIN = "admin"
    CLIENT = "client"


class FsmState(Model):
    key = fields.CharField(max_length=255, primary_key=True)
    state = fields.CharField(max_length=255, null=True)
    data = fields.JSONField(default=dict)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "fsm_state"


class User(Model):
    id = fields.BigIntField(primary_key=True)
    tg_id = fields.BigIntField(unique=True, index=True)
    username = fields.CharField(max_length=64, null=True)
    full_name = fields.CharField(max_length=255, null=True)
    role = fields.CharEnumField(Role, default=Role.CLIENT, max_length=16)
    # Overrides role for admins who want to use the bot as a client.
    active_role = fields.CharEnumField(Role, null=True, max_length=16)
    # Linked panel client email (clients only).
    panel_email = fields.CharField(max_length=255, null=True, index=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "bot_users"

    def __str__(self) -> str:  # pragma: no cover
        return f"User(tg_id={self.tg_id}, role={self.role})"

    @property
    def effective_role(self) -> Role:
        return self.active_role if self.active_role is not None else self.role

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_linked(self) -> bool:
        return bool(self.panel_email)

    @property
    def is_dual_role(self) -> bool:
        """True for admins who also have a linked panel client."""
        return self.role == Role.ADMIN and bool(self.panel_email)
