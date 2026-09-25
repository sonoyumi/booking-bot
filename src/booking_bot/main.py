"""Application wiring: settings, database, bot, reminder task."""

from __future__ import annotations

import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from booking_bot.config import load_settings
from booking_bot.db import Database
from booking_bot.handlers import router
from booking_bot.reminders import reminder_loop
from booking_bot.services import load_services

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    services = load_services(settings.services_path)
    db = await Database.open(settings.database_path)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    # Available to every handler as keyword arguments with the same names.
    dp["db"] = db
    dp["settings"] = settings
    dp["services"] = services

    reminders = asyncio.create_task(reminder_loop(bot, db, settings, services))
    logger.info("Bot started: %d services, admins: %d", len(services), len(settings.admin_ids))
    try:
        await dp.start_polling(bot)
    finally:
        reminders.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await reminders
        await db.close()
        await bot.session.close()
