"""Tortoise-ORM lifecycle helpers."""
from __future__ import annotations

from tortoise import Tortoise

from bot.db.models import FsmState, Role, User

MODELS = ["bot.db.models"]


async def init_db(db_url: str) -> None:
    await Tortoise.init(db_url=db_url, modules={"models": MODELS})
    await Tortoise.generate_schemas(safe=True)


async def close_db() -> None:
    await Tortoise.close_connections()


__all__ = ["init_db", "close_db", "FsmState", "User", "Role", "MODELS"]
