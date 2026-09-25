"""End-to-end flow through the real aiogram Dispatcher, with the network replaced by a recorder."""

from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.methods import AnswerCallbackQuery, EditMessageText, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from booking_bot.config import Settings
from booking_bot.db import Database
from booking_bot.handlers import router
from booking_bot.keyboards import CancelCb, ConfirmCb, DayCb, ServiceCb, SlotCb
from booking_bot.schedule import Schedule
from booking_bot.services import Service

TZ = ZoneInfo("Europe/Rome")
CLIENT = User(id=100, is_bot=False, first_name="Anna")
ADMIN_ID = 1
CHAT = Chat(id=CLIENT.id, type="private")


class RecordingSession(BaseSession):
    """Records every Bot API call instead of sending it."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list = []

    async def make_request(self, bot, method, timeout=None):  # noqa: ASYNC109 - signature set by aiogram
        self.calls.append(method)
        return True

    async def stream_content(self, *args, **kwargs):  # pragma: no cover - not used
        raise NotImplementedError

    async def close(self) -> None:
        pass

    def of(self, kind):
        return [c for c in self.calls if isinstance(c, kind)]


@pytest.fixture
async def env():
    session = RecordingSession()
    bot = Bot("42:TEST", session=session)
    db = await Database.open(":memory:")
    settings = Settings(
        bot_token="42:TEST",
        admin_ids=frozenset({ADMIN_ID}),
        schedule=Schedule(tz=TZ, work_start=9, work_end=18, work_days=frozenset(range(1, 8))),
        remind_before_minutes=120,
        database_path=Path(":memory:"),
        services_path=Path("unused.json"),
    )
    dp = Dispatcher()
    dp.include_router(router)
    dp["db"] = db
    dp["settings"] = settings
    dp["services"] = {"haircut": Service(id="haircut", title="Стрижка", price="25 €")}
    yield bot, dp, db, session
    await db.close()
    router._parent_router = None  # the module-level router can be attached to a new Dispatcher next test


def _message(text: str) -> Message:
    return Message(message_id=1, date=datetime.now(UTC), chat=CHAT, from_user=CLIENT, text=text)


async def send_text(bot, dp, text):
    await dp.feed_update(bot, Update(update_id=1, message=_message(text)))


async def press(bot, dp, data: str):
    query = CallbackQuery(id="q", from_user=CLIENT, chat_instance="ci", data=data, message=_message("menu"))
    await dp.feed_update(bot, Update(update_id=2, callback_query=query))


def tomorrow_at(hour: int) -> datetime:
    day = datetime.now(TZ).date() + timedelta(days=1)
    return datetime.combine(day, time(hour=hour), tzinfo=TZ)


async def test_full_booking_flow(env):
    bot, dp, db, session = env
    slot = tomorrow_at(10)

    await send_text(bot, dp, "/start")
    assert "Выберите услугу" in session.of(SendMessage)[-1].text

    await press(bot, dp, ServiceCb(service_id="haircut").pack())
    assert "Выберите день" in session.of(EditMessageText)[-1].text

    await press(bot, dp, DayCb(service_id="haircut", day=slot.date().isoformat()).pack())
    assert "Выберите время" in session.of(EditMessageText)[-1].text

    await press(bot, dp, SlotCb(service_id="haircut", ts=int(slot.timestamp())).pack())
    assert "Проверьте запись" in session.of(EditMessageText)[-1].text

    await press(bot, dp, ConfirmCb(service_id="haircut", ts=int(slot.timestamp())).pack())
    assert "Вы записаны" in session.of(EditMessageText)[-1].text
    admin_msgs = [m for m in session.of(SendMessage) if m.chat_id == ADMIN_ID]
    assert admin_msgs and "Новая запись" in admin_msgs[-1].text

    bookings = await db.user_bookings(CLIENT.id, datetime.now(UTC))
    assert len(bookings) == 1 and bookings[0].starts_at == slot

    # Every button press was answered, so the client never sees an endless spinner.
    assert len(session.of(AnswerCallbackQuery)) == 4  # service, day, slot, confirm

    await send_text(bot, dp, "/my")
    assert "Ваши записи" in session.of(SendMessage)[-1].text

    await press(bot, dp, CancelCb(booking_id=bookings[0].id).pack())
    assert "Запись отменена" in session.of(EditMessageText)[-1].text
    assert await db.user_bookings(CLIENT.id, datetime.now(UTC)) == []


async def test_taken_slot_shows_other_times(env):
    bot, dp, db, session = env
    slot = tomorrow_at(11)
    await db.book(user_id=999, user_name="Other", service_id="haircut", starts_at=slot)

    await press(bot, dp, ConfirmCb(service_id="haircut", ts=int(slot.timestamp())).pack())
    assert "только что заняли" in session.of(EditMessageText)[-1].text
    assert await db.user_bookings(CLIENT.id, datetime.now(UTC)) == []


async def test_forged_callback_is_rejected(env):
    bot, dp, db, session = env
    forged = tomorrow_at(10) + timedelta(minutes=7)  # not a real slot

    await press(bot, dp, ConfirmCb(service_id="haircut", ts=int(forged.timestamp())).pack())
    assert session.of(AnswerCallbackQuery)[-1].show_alert
    assert await db.user_bookings(CLIENT.id, datetime.now(UTC)) == []


async def test_today_is_admin_only(env):
    bot, dp, db, session = env
    await send_text(bot, dp, "/today")
    assert "только администратору" in session.of(SendMessage)[-1].text
