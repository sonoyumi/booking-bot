from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram.exceptions import TelegramForbiddenError
from aiogram.methods import SendMessage

from booking_bot.config import Settings
from booking_bot.db import Database
from booking_bot.reminders import send_due_reminders
from booking_bot.schedule import Schedule
from booking_bot.services import Service

NOW = datetime(2026, 9, 23, 10, 0, tzinfo=UTC)
SERVICES = {"haircut": Service(id="haircut", title="Стрижка")}
SETTINGS = Settings(
    bot_token="test",
    admin_ids=frozenset(),
    schedule=Schedule(tz=ZoneInfo("Europe/Rome")),
    remind_before_minutes=120,
    database_path=Path(":memory:"),
    services_path=Path("unused.json"),
)


class FakeBot:
    def __init__(self, blocked: set[int] = frozenset()):
        self.sent: list[tuple[int, str]] = []
        self.blocked = blocked

    async def send_message(self, chat_id: int, text: str) -> None:
        if chat_id in self.blocked:
            raise TelegramForbiddenError(method=SendMessage(chat_id=chat_id, text=text), message="blocked")
        self.sent.append((chat_id, text))


async def test_reminder_is_sent_once():
    db = await Database.open(":memory:")
    await db.book(user_id=7, user_name="Ann", service_id="haircut", starts_at=NOW + timedelta(hours=1))
    bot = FakeBot()

    assert await send_due_reminders(bot, db, SETTINGS, SERVICES, NOW) == 1
    assert bot.sent[0][0] == 7 and "Стрижка" in bot.sent[0][1]
    assert await send_due_reminders(bot, db, SETTINGS, SERVICES, NOW) == 0
    await db.close()


async def test_blocked_user_does_not_break_the_loop():
    db = await Database.open(":memory:")
    await db.book(user_id=1, user_name="Blocked", service_id="haircut", starts_at=NOW + timedelta(minutes=30))
    await db.book(user_id=2, user_name="Ok", service_id="haircut", starts_at=NOW + timedelta(minutes=90))
    bot = FakeBot(blocked={1})

    assert await send_due_reminders(bot, db, SETTINGS, SERVICES, NOW) == 1
    assert [chat for chat, _ in bot.sent] == [2]
    assert await db.due_reminders(NOW, timedelta(hours=2)) == []  # blocked one is not retried
    await db.close()
