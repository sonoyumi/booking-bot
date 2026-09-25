# 📅 Booking Bot

<p>
  <a href="https://github.com/sonoyumi/booking-bot/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/sonoyumi/booking-bot/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white">
  <img alt="aiogram" src="https://img.shields.io/badge/aiogram-3-2CA5E0?logo=telegram&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-aiosqlite-003B57?logo=sqlite&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

**🇬🇧 [English](#en)** · **🇷🇺 [Русский](#ru)**

---

<a name="en"></a>

## 🇬🇧 English

A Telegram bot for booking appointments at a salon, barbershop, studio or any small
business that works by appointment. Clients pick a service, a day and a free time slot
in a few taps; the bot reminds them before the visit, and the owner gets a notification
about every new booking and cancellation.

### Features

- **Booking in 4 taps:** service → day → free time → confirm. Past and taken slots are never shown.
- **No double bookings:** a partial UNIQUE index in SQLite guarantees one active booking per slot,
  even if two clients press "confirm" at the same moment.
- **"My bookings":** `/my` lists upcoming visits with one-tap cancellation; a cancelled slot becomes free again.
- **Reminders:** a background task reminds the client N minutes before the visit (once, even if the bot restarts).
- **For the owner:** notifications about new bookings and cancellations, `/today` shows today's schedule.
- **Configurable without code:** working hours, slot length, working days, time zone, booking horizon
  (`.env`) and the list of services with prices (`config/services.json`).
- **Safe by design:** callback data is validated (a forged time is rejected), user names are HTML-escaped,
  the bot token is never printed, personal data stays out of git.

### How it works

```
/start ─► choose service ─► choose day ─► choose free time ─► confirm
                                                                 │
                                   ┌─────────────────────────────┤
                                   ▼                             ▼
                        admin gets a notification     booking saved (SQLite)
                                                                 │
                                   reminder N minutes before ◄───┘
```

### Stack

`Python 3.11+` · `aiogram 3` · `aiosqlite` · `asyncio` · `zoneinfo` · `pytest` + `pytest-asyncio` · `ruff` · GitHub Actions

### Quick start

```bash
git clone https://github.com/sonoyumi/booking-bot.git
cd booking-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # set BOT_TOKEN (from @BotFather) and ADMIN_IDS
cp config/services.example.json config/services.json   # optional: your own services
booking-bot                   # or: python -m booking_bot
```

Tests: `pytest` (33 tests, including an end-to-end flow through the real aiogram Dispatcher).

### Project structure

```
src/booking_bot/
├── schedule.py   # working days and slots: pure logic, no Telegram
├── db.py         # SQLite storage, double-booking protection
├── handlers.py   # booking flow, /my, /today
├── keyboards.py  # inline keyboards and typed callback data
├── reminders.py  # background reminder task
├── services.py   # service catalog from JSON
├── config.py     # settings from .env
└── main.py       # wiring
```

### Author

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)), Python developer: Telegram bots, web scraping, automation.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)

> 💼 Need a booking bot for your business? Get in touch.

### License

MIT, see [LICENSE](LICENSE).

---

<a name="ru"></a>

## 🇷🇺 Русский

**[🇬🇧 English](#en)** · **🇷🇺 Русский**

Telegram-бот для записи клиентов в салон, барбершоп, студию или любой бизнес, который
работает по записи. Клиент в несколько нажатий выбирает услугу, день и свободное время,
бот напоминает о визите заранее, а владелец получает уведомление о каждой новой записи и отмене.

### Возможности

- **Запись в 4 нажатия:** услуга → день → свободное время → подтверждение. Прошедшие и занятые слоты не показываются.
- **Никаких двойных записей:** частичный UNIQUE-индекс в SQLite гарантирует одну активную запись на слот,
  даже если два клиента нажмут «Подтвердить» одновременно.
- **«Мои записи»:** `/my` показывает предстоящие визиты с отменой в одно нажатие; отменённое время снова становится свободным.
- **Напоминания:** фоновая задача напоминает клиенту за N минут до визита (один раз, даже после перезапуска бота).
- **Для владельца:** уведомления о новых записях и отменах, `/today` — расписание на сегодня.
- **Настраивается без кода:** рабочие часы, длительность слота, рабочие дни, часовой пояс, на сколько дней вперёд
  открыта запись (`.env`) и список услуг с ценами (`config/services.json`).
- **Безопасность:** данные кнопок проверяются (подделанное время отклоняется), имена клиентов экранируются,
  токен бота не попадает в логи, персональные данные не попадают в git.

### Как это работает

```
/start ─► выбор услуги ─► выбор дня ─► выбор свободного времени ─► подтверждение
                                                                         │
                                        ┌────────────────────────────────┤
                                        ▼                                ▼
                          админу приходит уведомление        запись сохранена (SQLite)
                                                                         │
                                        напоминание за N минут ◄─────────┘
```

### Стек

`Python 3.11+` · `aiogram 3` · `aiosqlite` · `asyncio` · `zoneinfo` · `pytest` + `pytest-asyncio` · `ruff` · GitHub Actions

### Быстрый старт

```bash
git clone https://github.com/sonoyumi/booking-bot.git
cd booking-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # вписать BOT_TOKEN (от @BotFather) и ADMIN_IDS
cp config/services.example.json config/services.json   # по желанию: свои услуги
booking-bot                   # или: python -m booking_bot
```

Тесты: `pytest` (33 теста, включая сквозной сценарий через настоящий Dispatcher aiogram).

### Структура проекта

```
src/booking_bot/
├── schedule.py   # рабочие дни и слоты: чистая логика без Telegram
├── db.py         # хранение в SQLite, защита от двойной записи
├── handlers.py   # сценарий записи, /my, /today
├── keyboards.py  # inline-клавиатуры и типизированные callback-данные
├── reminders.py  # фоновые напоминания
├── services.py   # каталог услуг из JSON
├── config.py     # настройки из .env
└── main.py       # сборка приложения
```

### Автор

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)) — Python-разработчик: Telegram-боты, парсинг, автоматизация.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)

> 💼 Нужен бот записи для вашего бизнеса? Напишите мне.

### Лицензия

MIT — см. [LICENSE](LICENSE).
