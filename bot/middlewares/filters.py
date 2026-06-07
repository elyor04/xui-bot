"""Reusable filters."""
from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from bot.db.models import Role, User


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject, user: User | None = None) -> bool:
        return bool(user and user.effective_role == Role.ADMIN)


class IsClient(BaseFilter):
    async def __call__(self, event: TelegramObject, user: User | None = None) -> bool:
        return bool(user and user.effective_role == Role.CLIENT)
