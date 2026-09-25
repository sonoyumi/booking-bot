from datetime import UTC, datetime, timedelta

import pytest

from booking_bot.db import Database, from_db, to_db

NOW = datetime(2026, 9, 23, 10, 0, tzinfo=UTC)
SLOT = NOW + timedelta(days=1)


@pytest.fixture
async def db():
    database = await Database.open(":memory:")
    yield database
    await database.close()


async def book(db, user_id=1, starts_at=SLOT):
    return await db.book(user_id=user_id, user_name=f"User {user_id}", service_id="haircut", starts_at=starts_at)


def test_timestamps_roundtrip_and_reject_naive():
    assert from_db(to_db(NOW)) == NOW
    with pytest.raises(ValueError):
        to_db(datetime(2026, 1, 1))


async def test_book_and_list(db):
    booking_id = await book(db)
    assert booking_id is not None
    bookings = await db.user_bookings(1, NOW)
    assert [b.id for b in bookings] == [booking_id]
    assert bookings[0].starts_at == SLOT


async def test_same_slot_cannot_be_booked_twice(db):
    assert await book(db, user_id=1) is not None
    assert await book(db, user_id=2) is None
    assert await db.booked_starts(NOW, SLOT + timedelta(hours=1)) == {SLOT}


async def test_cancel_frees_the_slot(db):
    booking_id = await book(db, user_id=1)
    cancelled = await db.cancel(booking_id, user_id=1)
    assert cancelled is not None and cancelled.status == "cancelled"
    assert await db.user_bookings(1, NOW) == []
    assert await book(db, user_id=2) is not None


async def test_cannot_cancel_someone_elses_booking(db):
    booking_id = await book(db, user_id=1)
    assert await db.cancel(booking_id, user_id=2) is None
    assert await db.cancel(booking_id, user_id=1) is not None
    assert await db.cancel(booking_id, user_id=1) is None  # already cancelled


async def test_past_bookings_are_not_listed(db):
    await book(db, starts_at=NOW - timedelta(hours=1))
    assert await db.user_bookings(1, NOW) == []


async def test_bookings_between(db):
    await book(db, user_id=1, starts_at=SLOT)
    await book(db, user_id=2, starts_at=SLOT + timedelta(days=2))
    found = await db.bookings_between(SLOT - timedelta(hours=1), SLOT + timedelta(hours=1))
    assert [b.user_id for b in found] == [1]


async def test_due_reminders_window_and_mark(db):
    soon = await book(db, user_id=1, starts_at=NOW + timedelta(hours=1))
    await book(db, user_id=2, starts_at=NOW + timedelta(hours=5))
    due = await db.due_reminders(NOW, timedelta(hours=2))
    assert [b.id for b in due] == [soon]
    await db.mark_reminded(soon)
    assert await db.due_reminders(NOW, timedelta(hours=2)) == []
