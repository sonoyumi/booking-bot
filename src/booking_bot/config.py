"""Settings from environment variables (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

from booking_bot.schedule import Schedule

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    bot_token: str = field(repr=False)  # never printed in logs or tracebacks
    admin_ids: frozenset[int]
    schedule: Schedule
    remind_before_minutes: int
    database_path: Path
    services_path: Path


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from None


def _int_set(name: str, default: str = "") -> frozenset[int]:
    raw = os.getenv(name, default)
    try:
        return frozenset(int(part) for part in raw.replace(" ", "").split(",") if part)
    except ValueError:
        raise ValueError(f"{name} must be a comma-separated list of integers, got {raw!r}") from None


def _path(name: str, default: str) -> Path:
    path = Path(os.getenv(name, "").strip() or default)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")

    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is not set: copy .env.example to .env and fill it in")

    tz_name = os.getenv("TIMEZONE", "").strip() or "Europe/Rome"
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Unknown TIMEZONE {tz_name!r}, use a name like Europe/Rome") from None

    schedule = Schedule(
        tz=tz,
        work_start=_int("WORK_START", 10),
        work_end=_int("WORK_END", 19),
        slot_minutes=_int("SLOT_MINUTES", 60),
        days_ahead=_int("DAYS_AHEAD", 7),
        work_days=_int_set("WORK_DAYS", "1,2,3,4,5,6"),
    )
    return Settings(
        bot_token=token,
        admin_ids=_int_set("ADMIN_IDS"),
        schedule=schedule,
        remind_before_minutes=_int("REMIND_BEFORE_MINUTES", 120),
        database_path=_path("DATABASE_PATH", "data/bookings.db"),
        services_path=_path("SERVICES_PATH", "config/services.json"),
    )
