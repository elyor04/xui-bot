"""Entry point: wire config, DB, API client, dispatcher and start polling.

Run with:  python -m bot
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from bot.api import XUIClient
from bot.config import get_settings
from bot.db import close_db, init_db
from bot.db.fsm import TortoiseStorage
from bot.handlers import build_router
from bot.middlewares.auth import AuthMiddleware
from bot.tasks.report import send_report

logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="[%(asctime)s] - %(levelname)s - %(name)s - %(message)s",
)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)

logger = logging.getLogger("xui_bot")


async def main() -> None:
    settings = get_settings()

    await init_db(settings.db_url)
    logger.info("Database ready (%s)", settings.db_url.split("://", 1)[0])

    api = XUIClient(settings)
    await api.start()
    try:
        await api.login()
        logger.info("Authenticated against panel %s", settings.api_base)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Panel auth not verified yet: %s", exc)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=TortoiseStorage())

    dp["settings"] = settings
    dp["api"] = api

    auth = AuthMiddleware(settings)
    dp.message.outer_middleware(auth)
    dp.callback_query.outer_middleware(auth)

    dp.include_router(build_router())

    scheduler = AsyncIOScheduler()
    if settings.report_interval_hours and settings.admin_ids:
        scheduler.add_job(
            send_report,
            IntervalTrigger(hours=settings.report_interval_hours),
            args=[bot, api, settings],
        )
        logger.info("Periodic report scheduled every %sh", settings.report_interval_hours)

    try:
        me = await bot.get_me()
        logger.info("Starting @%s …", me.username)
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Open the menu"),
                BotCommand(command="cancel", description="Cancel current action"),
            ],
            scope=BotCommandScopeAllPrivateChats(),
        )
        await bot.delete_webhook(drop_pending_updates=True)
        scheduler.start()
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await api.close()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    try:
        import uvloop  # type: ignore[import]
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logger.info("Using uvloop")
    except ImportError:
        pass

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped.")
