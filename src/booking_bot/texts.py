"""User-facing texts and formatting."""

from __future__ import annotations

from datetime import date, datetime, tzinfo
from html import escape

WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")

START = "👋 Здравствуйте! Я помогу записаться на приём.\n\nВыберите услугу:"
HELP = "<b>Как записаться</b>\n/start — выбрать услугу, день и время\n/my — мои записи и отмена\n/help — эта подсказка"
ADMIN_HELP = "\n\n<b>Для администратора</b>\n/today — записи на сегодня"
UNKNOWN = "Не понял сообщение 🙂 Нажмите /start, чтобы записаться, или /my, чтобы посмотреть записи."
SLOT_TAKEN = "😔 Это время только что заняли. Выберите другое:"
SLOT_UNAVAILABLE = "Это время уже недоступно. Выберите другое."
SERVICE_UNAVAILABLE = "Эта услуга больше недоступна."
NO_BOOKINGS = "У вас нет предстоящих записей. Записаться: /start"
ADMIN_ONLY = "Эта команда доступна только администратору."


def day_label(day: date) -> str:
    return f"{WEEKDAYS[day.weekday()]} {day:%d.%m}"


def when(value: datetime, tz: tzinfo) -> str:
    local = value.astimezone(tz)
    return f"{day_label(local.date())} в {local:%H:%M}"


def user_link(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{escape(name)}</a>'
