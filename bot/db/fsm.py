"""Tortoise-ORM-backed FSM storage for aiogram v3."""
from __future__ import annotations

from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

from bot.db.models import FsmState


def _key(key: StorageKey) -> str:
    return f"{key.bot_id}:{key.chat_id}:{key.user_id}:{key.destiny}"


class TortoiseStorage(BaseStorage):
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        state_str = state.state if isinstance(state, State) else state
        await FsmState.update_or_create(key=_key(key), defaults={"state": state_str})

    async def get_state(self, key: StorageKey) -> str | None:
        obj = await FsmState.get_or_none(key=_key(key))
        return obj.state if obj else None

    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None:
        await FsmState.update_or_create(key=_key(key), defaults={"data": data})

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        obj = await FsmState.get_or_none(key=_key(key))
        return obj.data if obj else {}

    async def close(self) -> None:
        pass  # Tortoise lifecycle is managed by init_db / close_db
