"""Telegram handlers: the booking flow, "my bookings", and admin commands."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from booking_bot import texts
from booking_bot.config import Settings
from booking_bot.db import Database
from booking_bot.keyboards import (
    MENU,
    CancelCb,
    ConfirmCb,
    DayCb,
    ServiceCb,
    SlotCb,
    confirm_kb,
    days_kb,
    my_bookings_kb,
    services_kb,
    slots_kb,
)
from booking_bot.services import Service, service_title

logger = logging.getLogger(__name__)

router = Router()
# Bookings contain personal data: work in private chats only.
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


def _now() -> datetime:
    return datetime.now(UTC)


async def _show(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    """Edits the message the button belongs to; always answers the callback (no endless spinner)."""
    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc):
                raise
    await callback.answer()


async def _notify_admins(bot: Bot, settings: Settings, text: str) -> None:
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except (TelegramForbiddenError, TelegramBadRequest):
            logger.warning("Cannot notify admin %s (did they start the bot?)", admin_id)


async def _day_screen(
    callback: CallbackQuery, db: Database, settings: Settings, service: Service, day: date, prefix: str = ""
) -> None:
    schedule = settings.schedule
    slots = schedule.slots(day)
    booked = await db.booked_starts(slots[0], slots[-1] + schedule.slot) if slots else set()
    free = schedule.free_slots(day, booked, _now())
    if not free:
        text = f"{prefix}<b>{service.title}</b>, {texts.day_label(day)}: свободного времени нет. Выберите другой день:"
        await _show(callback, text, days_kb(service.id, schedule.days(_now())))
        return
    text = f"{prefix}<b>{service.title}</b>, {texts.day_label(day)}. Выберите время:"
    await _show(callback, text, slots_kb(service.id, free, schedule.tz))


# --- booking flow: service -> day -> time -> confirm -------------------------------------------


@router.message(CommandStart())
async def cmd_start(message: Message, services: dict[str, Service]) -> None:
    await message.answer(texts.START, reply_markup=services_kb(services.values()))


@router.callback_query(F.data == MENU)
async def on_menu(callback: CallbackQuery, services: dict[str, Service]) -> None:
    await _show(callback, texts.START, services_kb(services.values()))


@router.callback_query(ServiceCb.filter())
async def on_service(
    callback: CallbackQuery, callback_data: ServiceCb, settings: Settings, services: dict[str, Service]
) -> None:
    service = services.get(callback_data.service_id)
    if service is None:
        await callback.answer(texts.SERVICE_UNAVAILABLE, show_alert=True)
        return
    days = settings.schedule.days(_now())
    await _show(callback, f"<b>{service.title}</b>. Выберите день:", days_kb(service.id, days))


@router.callback_query(DayCb.filter())
async def on_day(
    callback: CallbackQuery,
    callback_data: DayCb,
    db: Database,
    settings: Settings,
    services: dict[str, Service],
) -> None:
    service = services.get(callback_data.service_id)
    try:
        day = date.fromisoformat(callback_data.day)
    except ValueError:
        day = None
    if service is None or day not in settings.schedule.days(_now()):
        await callback.answer(texts.SLOT_UNAVAILABLE, show_alert=True)
        return
    await _day_screen(callback, db, settings, service, day)


@router.callback_query(SlotCb.filter())
async def on_slot(
    callback: CallbackQuery, callback_data: SlotCb, settings: Settings, services: dict[str, Service]
) -> None:
    service = services.get(callback_data.service_id)
    slot = datetime.fromtimestamp(callback_data.ts, UTC)
    if service is None or not settings.schedule.is_bookable(slot, _now()):
        await callback.answer(texts.SLOT_UNAVAILABLE, show_alert=True)
        return
    price = f"\nСтоимость: {service.price}" if service.price else ""
    text = f"Проверьте запись:\n\n<b>{service.title}</b>\n🗓 {texts.when(slot, settings.schedule.tz)}{price}"
    await _show(callback, text, confirm_kb(service.id, slot, settings.schedule.tz))


@router.callback_query(ConfirmCb.filter())
async def on_confirm(
    callback: CallbackQuery,
    callback_data: ConfirmCb,
    bot: Bot,
    db: Database,
    settings: Settings,
    services: dict[str, Service],
) -> None:
    service = services.get(callback_data.service_id)
    slot = datetime.fromtimestamp(callback_data.ts, UTC)
    if service is None or not settings.schedule.is_bookable(slot, _now()):
        await callback.answer(texts.SLOT_UNAVAILABLE, show_alert=True)
        return

    user = callback.from_user
    booking_id = await db.book(user_id=user.id, user_name=user.full_name, service_id=service.id, starts_at=slot)
    tz = settings.schedule.tz
    if booking_id is None:
        await _day_screen(callback, db, settings, service, slot.astimezone(tz).date(), prefix=texts.SLOT_TAKEN + "\n\n")
        return

    await _show(
        callback,
        f"✅ Вы записаны!\n\n<b>{service.title}</b>\n🗓 {texts.when(slot, tz)}\n\n"
        f"Я напомню заранее. Посмотреть или отменить запись: /my",
    )
    await _notify_admins(
        bot,
        settings,
        f"🆕 Новая запись #{booking_id}\n{texts.user_link(user.id, user.full_name)}\n"
        f"<b>{service.title}</b>, {texts.when(slot, tz)}",
    )


# --- my bookings -------------------------------------------------------------------------------


@router.message(Command("my"))
async def cmd_my(message: Message, db: Database, settings: Settings, services: dict[str, Service]) -> None:
    if message.from_user is None:
        return
    bookings = await db.user_bookings(message.from_user.id, _now())
    if not bookings:
        await message.answer(texts.NO_BOOKINGS)
        return
    tz = settings.schedule.tz
    lines = [f"• <b>{service_title(services, b.service_id)}</b>, {texts.when(b.starts_at, tz)}" for b in bookings]
    await message.answer(
        "Ваши записи:\n\n" + "\n".join(lines) + "\n\nЧтобы отменить, нажмите кнопку ниже.",
        reply_markup=my_bookings_kb(bookings, services, tz),
    )


@router.callback_query(CancelCb.filter())
async def on_cancel(
    callback: CallbackQuery,
    callback_data: CancelCb,
    bot: Bot,
    db: Database,
    settings: Settings,
    services: dict[str, Service],
) -> None:
    user = callback.from_user
    booking = await db.cancel(callback_data.booking_id, user.id)
    if booking is None:
        await callback.answer("Эта запись уже отменена или прошла.", show_alert=True)
        return
    tz = settings.schedule.tz
    title = service_title(services, booking.service_id)
    await _show(
        callback, f"Запись отменена: <b>{title}</b>, {texts.when(booking.starts_at, tz)}.\n\nЗаписаться снова: /start"
    )
    await _notify_admins(
        bot,
        settings,
        f"❌ Отмена записи #{booking.id}\n{texts.user_link(user.id, user.full_name)}\n"
        f"<b>{title}</b>, {texts.when(booking.starts_at, tz)}",
    )


# --- admin & misc ------------------------------------------------------------------------------


@router.message(Command("today"))
async def cmd_today(message: Message, db: Database, settings: Settings, services: dict[str, Service]) -> None:
    if message.from_user is None or message.from_user.id not in settings.admin_ids:
        await message.answer(texts.ADMIN_ONLY)
        return
    tz = settings.schedule.tz
    start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    bookings = await db.bookings_between(start, start + timedelta(days=1))
    if not bookings:
        await message.answer("На сегодня записей нет.")
        return
    lines = [
        f"{b.starts_at.astimezone(tz):%H:%M} — "
        f"{service_title(services, b.service_id)}, "
        f"{texts.user_link(b.user_id, b.user_name)}"
        for b in bookings
    ]
    await message.answer(f"<b>Записи на сегодня ({len(bookings)}):</b>\n\n" + "\n".join(lines))


@router.message(Command("help"))
async def cmd_help(message: Message, settings: Settings) -> None:
    is_admin = message.from_user is not None and message.from_user.id in settings.admin_ids
    await message.answer(texts.HELP + (texts.ADMIN_HELP if is_admin else ""))


@router.message()
async def fallback(message: Message) -> None:
    await message.answer(texts.UNKNOWN)
