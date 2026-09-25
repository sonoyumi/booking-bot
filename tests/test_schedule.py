from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from booking_bot.schedule import Schedule

TZ = ZoneInfo("Europe/Rome")
# Wednesday, 12:30 local time
NOW = datetime(2026, 9, 23, 12, 30, tzinfo=TZ)


def make(**kwargs) -> Schedule:
    return Schedule(tz=TZ, **kwargs)


def test_days_skip_non_working_days():
    days = make(days_ahead=7, work_days=frozenset({1, 2, 3, 4, 5})).days(NOW)
    assert days[0] == date(2026, 9, 23)
    assert all(d.isoweekday() <= 5 for d in days)
    assert len(days) == 5  # Wed..Tue minus Sat and Sun


def test_slots_fit_working_hours():
    slots = make(work_start=10, work_end=13, slot_minutes=60).slots(date(2026, 9, 23))
    assert [s.hour for s in slots] == [10, 11, 12]
    assert all(s.tzinfo is TZ for s in slots)


def test_last_partial_slot_is_dropped():
    slots = make(work_start=10, work_end=11, slot_minutes=45).slots(date(2026, 9, 23))
    assert len(slots) == 1  # 10:00-10:45 fits, 10:45-11:30 does not


def test_free_slots_exclude_past_and_booked():
    schedule = make(work_start=10, work_end=16)
    today = NOW.date()
    booked = {datetime(2026, 9, 23, 14, 0, tzinfo=TZ)}
    free = schedule.free_slots(today, booked, NOW)
    assert [s.hour for s in free] == [13, 15]


def test_booked_set_matches_across_timezones():
    schedule = make(work_start=10, work_end=12)
    booked_utc = {datetime(2026, 9, 24, 10, 0, tzinfo=TZ).astimezone(ZoneInfo("UTC"))}
    free = schedule.free_slots(date(2026, 9, 24), booked_utc, NOW)
    assert [s.hour for s in free] == [11]


def test_is_bookable_rejects_forged_times():
    schedule = make(work_start=10, work_end=19, days_ahead=3)
    tomorrow_11 = datetime(2026, 9, 24, 11, 0, tzinfo=TZ)
    assert schedule.is_bookable(tomorrow_11, NOW)
    assert not schedule.is_bookable(tomorrow_11 + timedelta(minutes=7), NOW)  # not a slot boundary
    assert not schedule.is_bookable(datetime(2026, 9, 23, 11, 0, tzinfo=TZ), NOW)  # in the past
    assert not schedule.is_bookable(datetime(2026, 9, 24, 21, 0, tzinfo=TZ), NOW)  # after hours
    assert not schedule.is_bookable(datetime(2026, 10, 5, 11, 0, tzinfo=TZ), NOW)  # too far ahead


@pytest.mark.parametrize(
    "kwargs",
    [
        {"work_start": 19, "work_end": 10},
        {"slot_minutes": 0},
        {"days_ahead": 0},
        {"work_days": frozenset({0, 8})},
    ],
)
def test_invalid_schedule_is_rejected(kwargs):
    with pytest.raises(ValueError):
        make(**kwargs)
