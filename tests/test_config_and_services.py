import json

import pytest

from booking_bot import config
from booking_bot.keyboards import ConfirmCb, SlotCb
from booking_bot.services import load_services


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)  # no real .env is read
    for name in ("BOT_TOKEN", "ADMIN_IDS", "TIMEZONE", "WORK_START", "WORK_END", "WORK_DAYS"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_missing_token_is_a_clear_error(env):
    with pytest.raises(RuntimeError, match="BOT_TOKEN"):
        config.load_settings()


def test_settings_parse_and_hide_token(env, tmp_path):
    env.setenv("BOT_TOKEN", "123:secret")
    env.setenv("ADMIN_IDS", "1, 2")
    env.setenv("WORK_DAYS", "1,2,3")
    settings = config.load_settings()
    assert settings.admin_ids == {1, 2}
    assert settings.schedule.work_days == {1, 2, 3}
    assert settings.database_path == tmp_path / "data/bookings.db"
    assert "secret" not in repr(settings)


def test_bad_values_are_reported(env):
    env.setenv("BOT_TOKEN", "123:secret")
    env.setenv("WORK_START", "ten")
    with pytest.raises(ValueError, match="WORK_START"):
        config.load_settings()
    env.setenv("WORK_START", "10")
    env.setenv("TIMEZONE", "Mars/Base")
    with pytest.raises(ValueError, match="TIMEZONE"):
        config.load_settings()


def test_example_catalog_is_used_as_fallback(tmp_path):
    (tmp_path / "services.example.json").write_text(
        json.dumps([{"id": "cut", "title": "Cut", "price": "10"}]), encoding="utf-8"
    )
    services = load_services(tmp_path / "services.json")
    assert services["cut"].label == "Cut · 10"


@pytest.mark.parametrize(
    "data",
    [
        [],
        [{"id": "bad id", "title": "x"}],
        [{"id": "a", "title": "x"}, {"id": "a", "title": "y"}],
    ],
)
def test_invalid_catalog_is_rejected(tmp_path, data):
    path = tmp_path / "services.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        load_services(path)


def test_shipped_example_catalog_is_valid():
    services = load_services(config.PROJECT_ROOT / "config" / "services.json")
    assert services


def test_callback_data_fits_telegram_limit():
    # Telegram allows at most 64 bytes of callback data.
    longest_id = "x" * 24
    for cb in (SlotCb(service_id=longest_id, ts=4_102_444_800), ConfirmCb(service_id=longest_id, ts=4_102_444_800)):
        assert len(cb.pack().encode()) <= 64
