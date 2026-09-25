"""Working schedule: which days and time slots can be booked.

Pure logic with no Telegram and no database, so it is trivial to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, tzinfo


@dataclass(frozen=True)
class Schedule:
    tz: tzinfo
    work_start: int = 10  # first slot starts at this hour
    work_end: int = 19  # last slot must end by this hour
    slot_minutes: int = 60
    days_ahead: int = 7  # how many days (from today) are open for booking
    work_days: frozenset[int] = field(default_factory=lambda: frozenset({1, 2, 3, 4, 5, 6}))  # ISO: 1=Mon

    def __post_init__(self) -> None:
        if not 0 <= self.work_start < self.work_end <= 24:
            raise ValueError("Expected 0 <= WORK_START < WORK_END <= 24")
        if self.slot_minutes <= 0:
            raise ValueError("SLOT_MINUTES must be positive")
        if self.days_ahead < 1:
            raise ValueError("DAYS_AHEAD must be at least 1")
        if not self.work_days or not self.work_days <= set(range(1, 8)):
            raise ValueError("WORK_DAYS must contain ISO weekdays 1..7")

    @property
    def slot(self) -> timedelta:
        return timedelta(minutes=self.slot_minutes)

    def days(self, now: datetime) -> list[date]:
        """Working days open for booking, starting from today (in the schedule's timezone)."""
        today = now.astimezone(self.tz).date()
        candidates = (today + timedelta(days=i) for i in range(self.days_ahead))
        return [d for d in candidates if d.isoweekday() in self.work_days]

    def slots(self, day: date) -> list[datetime]:
        """Start times of every slot of a day, as timezone-aware datetimes."""
        start = datetime.combine(day, time(hour=self.work_start), tzinfo=self.tz)
        end = start + timedelta(hours=self.work_end - self.work_start)
        result = []
        current = start
        while current + self.slot <= end:
            result.append(current)
            current += self.slot
        return result

    def free_slots(self, day: date, booked: set[datetime], now: datetime) -> list[datetime]:
        """Slots of a day that are still in the future and not taken."""
        return [s for s in self.slots(day) if s > now and s not in booked]

    def is_bookable(self, starts_at: datetime, now: datetime) -> bool:
        """Guards against forged callback data: the time must be a real, future slot."""
        day = starts_at.astimezone(self.tz).date()
        return day in self.days(now) and starts_at > now and starts_at in self.slots(day)
