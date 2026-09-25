"""Inline keyboards and typed callback data."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, tzinfo

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from booking_bot.db import Booking
from booking_bot.services import Service, service_title
from booking_bot.texts import day_label, when

MENU = "menu"


class ServiceCb(CallbackData, prefix="svc"):
    service_id: str


class DayCb(CallbackData, prefix="day"):
    service_id: str
    day: str  # ISO date


class SlotCb(CallbackData, prefix="slot"):
    service_id: str
    ts: int  # unix timestamp of the slot start


class ConfirmCb(CallbackData, prefix="ok"):
    service_id: str
    ts: int


class CancelCb(CallbackData, prefix="cancel"):
    booking_id: int


def services_kb(services: Iterable[Service]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for service in services:
        kb.button(text=service.label, callback_data=ServiceCb(service_id=service.id))
    kb.adjust(1)
    return kb.as_markup()


def days_kb(service_id: str, days: Iterable[date]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for day in days:
        kb.button(text=day_label(day), callback_data=DayCb(service_id=service_id, day=day.isoformat()))
    kb.adjust(3)
    kb.row(InlineKeyboardButton(text="← Услуги", callback_data=MENU))
    return kb.as_markup()


def slots_kb(service_id: str, slots: Iterable[datetime], tz: tzinfo) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for slot in slots:
        kb.button(
            text=f"{slot.astimezone(tz):%H:%M}",
            callback_data=SlotCb(service_id=service_id, ts=int(slot.timestamp())),
        )
    kb.adjust(4)
    kb.row(InlineKeyboardButton(text="← Дни", callback_data=ServiceCb(service_id=service_id).pack()))
    return kb.as_markup()


def confirm_kb(service_id: str, slot: datetime, tz: tzinfo) -> InlineKeyboardMarkup:
    day = slot.astimezone(tz).date().isoformat()
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data=ConfirmCb(service_id=service_id, ts=int(slot.timestamp())))
    kb.button(text="← Другое время", callback_data=DayCb(service_id=service_id, day=day))
    kb.adjust(1)
    return kb.as_markup()


def my_bookings_kb(bookings: Iterable[Booking], services: dict[str, Service], tz: tzinfo) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for booking in bookings:
        title = service_title(services, booking.service_id)
        kb.button(
            text=f"❌ Отменить: {title}, {when(booking.starts_at, tz)}",
            callback_data=CancelCb(booking_id=booking.id),
        )
    kb.adjust(1)
    return kb.as_markup()
