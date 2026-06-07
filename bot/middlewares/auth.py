"""Middleware that resolves (and lazily creates) the local :class:`User` row
for the sender, promotes configured admins, and injects the row into handlers
as ``user``.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User as TgUser

from bot.config import Settings
from bot.db.models import Role, User
from bot.utils.formatting import get_tz


class AuthMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings) -> None:
        self._admin_ids = set(settings.admin_ids)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        if tg_user is None and isinstance(event, (Message, CallbackQuery)):
            tg_user = event.from_user
        if tg_user is None:
            return await handler(event, data)

        user, created = await User.get_or_create(
            tg_id=tg_user.id,
            defaults={
                "username": tg_user.username,
                "full_name": tg_user.full_name,
                "role": Role.ADMIN if tg_user.id in self._admin_ids else Role.CLIENT,
            },
        )

        desired_role = Role.ADMIN if tg_user.id in self._admin_ids else user.role
        changed = False
        if user.role != desired_role:
            user.role = desired_role
            changed = True
        if user.username != tg_user.username or user.full_name != tg_user.full_name:
            user.username = tg_user.username
            user.full_name = tg_user.full_name
            changed = True
        if changed and not created:
            await user.save()

        data["user"] = user
        data["lang"] = user.language or "en"
        data["tz"] = get_tz(user.timezone or "UTC")
        return await handler(event, data)
