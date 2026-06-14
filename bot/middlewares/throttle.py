"""Per-user rate-limit middleware.

Drops events that arrive faster than ``cooldown`` seconds from the same user.
Admins are exempt so menu navigation stays responsive for them.
"""
from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

_DEFAULT_COOLDOWN = 0.2  # seconds


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: set[int], cooldown: float = _DEFAULT_COOLDOWN) -> None:
        self._admin_ids = admin_ids
        self._cooldown = cooldown
        self._last: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = data.get("event_from_user")
        if from_user is None or from_user.id in self._admin_ids:
            return await handler(event, data)

        now = time.monotonic()
        uid = from_user.id
        if now - self._last.get(uid, 0.0) < self._cooldown:
            if isinstance(event, CallbackQuery):
                await event.answer()  # dismiss the loading spinner
            return None

        self._last[uid] = now
        return await handler(event, data)
