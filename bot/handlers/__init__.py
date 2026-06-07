"""Aggregate every router into one, included by the dispatcher."""
from __future__ import annotations

from aiogram import Router

from bot.handlers import common
from bot.handlers.admin import clients as admin_clients
from bot.handlers.admin import menu as admin_menu
from bot.handlers.client import account as client_account


def build_router() -> Router:
    root = Router(name="root")
    # Order matters: common first (home/cancel), then role-scoped routers.
    root.include_router(common.router)
    root.include_router(admin_menu.router)
    root.include_router(admin_clients.router)
    root.include_router(client_account.router)
    return root
