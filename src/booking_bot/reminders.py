"""Background task that reminds clients about upcoming bookings."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Protocol

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from booking_bot.config import Settings
from booking_bot.db import Database
from booking_bot.services import Service, service_title
from booking_bot.texts import when

logger = logging.getLogger(__name__)


class MessageSender(Protocol):
    async def send_message(self, chat_id: int, text: str) -> object: ...


async def send_due_reminders(
    bot: MessageSender, db: Database, settings: Settings, services: dict[str, Service], now: datetime
) -> int:
    """Sends reminders that are due; returns how many were sent."""
    sent = 0
    before = timedelta(minutes=settings.remind_before_minutes)
    for booking in await db.due_reminders(now, before):
        title = service_title(services, booking.service_id)
        text = (
            f"⏰ Напоминание: <b>{title}</b>, {when(booking.starts_at, settings.schedule.tz)}.\n"
            f"Если планы изменились, отмените запись: /my"
        )
        try:
            await bot.send_message(booking.user_id, text)
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            logger.info("Client %s blocked the bot, reminder skipped", booking.user_id)
        # Marked even when delivery failed: retrying a blocked user every minute is pointless.
        await db.mark_reminded(booking.id)
    return sent


async def reminder_loop(
    bot: MessageSender, db: Database, settings: Settings, services: dict[str, Service], interval: float = 60
) -> None:
    while True:
        try:
            await send_due_reminders(bot, db, settings, services, datetime.now(UTC))
        except Exception:  # the loop must survive any single failure
            logger.exception("Reminder check failed")
        await asyncio.sleep(interval)
