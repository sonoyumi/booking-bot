"""SQLite storage for bookings (aiosqlite)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

# Fixed-width UTC timestamps: string comparison in SQL == chronological comparison.
_TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    user_name   TEXT    NOT NULL,
    service_id  TEXT    NOT NULL,
    starts_at   TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'active',
    reminded    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL
);
-- One active booking per slot, enforced by the database itself: two users pressing
-- "confirm" at the same moment cannot both get the slot.
CREATE UNIQUE INDEX IF NOT EXISTS ux_bookings_active_slot ON bookings (starts_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS ix_bookings_user ON bookings (user_id, status);
"""


def to_db(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("naive datetime: pass a timezone-aware value")
    return value.astimezone(UTC).strftime(_TS_FORMAT)


def from_db(value: str) -> datetime:
    return datetime.strptime(value, _TS_FORMAT).replace(tzinfo=UTC)


@dataclass(frozen=True)
class Booking:
    id: int
    user_id: int
    user_name: str
    service_id: str
    starts_at: datetime
    status: str


def _booking(row: aiosqlite.Row) -> Booking:
    return Booking(
        id=row["id"],
        user_id=row["user_id"],
        user_name=row["user_name"],
        service_id=row["service_id"],
        starts_at=from_db(row["starts_at"]),
        status=row["status"],
    )


class Database:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    @classmethod
    async def open(cls, path: Path | str) -> Database:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(path)
        conn.row_factory = aiosqlite.Row
        await conn.executescript(SCHEMA)
        await conn.commit()
        return cls(conn)

    async def close(self) -> None:
        await self._conn.close()

    async def book(self, *, user_id: int, user_name: str, service_id: str, starts_at: datetime) -> int | None:
        """Returns the new booking id, or None if the slot is already taken."""
        try:
            cursor = await self._conn.execute(
                "INSERT INTO bookings (user_id, user_name, service_id, starts_at, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, user_name, service_id, to_db(starts_at), to_db(datetime.now(UTC))),
            )
        except sqlite3.IntegrityError:
            await self._conn.rollback()
            return None
        await self._conn.commit()
        return cursor.lastrowid

    async def booked_starts(self, start: datetime, end: datetime) -> set[datetime]:
        """Start times of active bookings in [start, end)."""
        async with self._conn.execute(
            "SELECT starts_at FROM bookings WHERE status = 'active' AND starts_at >= ? AND starts_at < ?",
            (to_db(start), to_db(end)),
        ) as cursor:
            return {from_db(row["starts_at"]) async for row in cursor}

    async def get(self, booking_id: int) -> Booking | None:
        async with self._conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)) as cursor:
            row = await cursor.fetchone()
        return _booking(row) if row else None

    async def user_bookings(self, user_id: int, now: datetime) -> list[Booking]:
        """Upcoming active bookings of a user, soonest first."""
        async with self._conn.execute(
            "SELECT * FROM bookings WHERE user_id = ? AND status = 'active' AND starts_at > ? ORDER BY starts_at",
            (user_id, to_db(now)),
        ) as cursor:
            return [_booking(row) async for row in cursor]

    async def cancel(self, booking_id: int, user_id: int) -> Booking | None:
        """Cancels a user's own active booking; returns it, or None if there was nothing to cancel."""
        cursor = await self._conn.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = ? AND user_id = ? AND status = 'active'",
            (booking_id, user_id),
        )
        await self._conn.commit()
        if cursor.rowcount == 0:
            return None
        return await self.get(booking_id)

    async def bookings_between(self, start: datetime, end: datetime) -> list[Booking]:
        async with self._conn.execute(
            "SELECT * FROM bookings WHERE status = 'active' AND starts_at >= ? AND starts_at < ? ORDER BY starts_at",
            (to_db(start), to_db(end)),
        ) as cursor:
            return [_booking(row) async for row in cursor]

    async def due_reminders(self, now: datetime, before: timedelta) -> list[Booking]:
        """Active bookings starting within `before` from now that were not reminded yet."""
        async with self._conn.execute(
            "SELECT * FROM bookings WHERE status = 'active' AND reminded = 0 "
            "AND starts_at > ? AND starts_at <= ? ORDER BY starts_at",
            (to_db(now), to_db(now + before)),
        ) as cursor:
            return [_booking(row) async for row in cursor]

    async def mark_reminded(self, booking_id: int) -> None:
        await self._conn.execute("UPDATE bookings SET reminded = 1 WHERE id = ?", (booking_id,))
        await self._conn.commit()
