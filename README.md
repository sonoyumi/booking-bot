# 📅 Booking Bot

<p>
  <a href="https://github.com/sonoyumi/booking-bot/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/sonoyumi/booking-bot/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white">
  <img alt="aiogram" src="https://img.shields.io/badge/aiogram-3-2CA5E0?logo=telegram&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-aiosqlite-003B57?logo=sqlite&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

**🇬🇧 [English](#en)** · **🇮🇹 [Italiano](#it)** · **🇺🇦 [Українська](#uk)** · **🇷🇺 [Русский](#ru)**

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

<a name="it"></a>

## 🇮🇹 Italiano

**[🇬🇧 English](#en)** · **🇮🇹 Italiano** · **[🇺🇦 Українська](#uk)** · **[🇷🇺 Русский](#ru)**

Un bot Telegram per prenotare appuntamenti in un salone, un barbiere, uno studio o qualsiasi piccola
attività che lavora su appuntamento. Il cliente sceglie un servizio, un giorno e un orario libero
in pochi tocchi; il bot gli ricorda la visita in anticipo e il titolare riceve una notifica
per ogni nuova prenotazione e ogni disdetta.

### Funzionalità

- **Prenotazione in 4 tocchi:** servizio → giorno → orario libero → conferma. Gli orari passati e quelli occupati non vengono mai mostrati.
- **Niente doppie prenotazioni:** un indice UNIQUE parziale in SQLite garantisce una sola prenotazione attiva per fascia oraria,
  anche se due clienti premono "conferma" nello stesso istante.
- **"Le mie prenotazioni":** `/my` elenca le visite in programma con disdetta in un tocco; la fascia disdetta torna libera.
- **Promemoria:** un'attività in background ricorda al cliente la visita N minuti prima (una sola volta, anche se il bot viene riavviato).
- **Per il titolare:** notifiche su nuove prenotazioni e disdette, `/today` mostra l'agenda di oggi.
- **Configurabile senza codice:** orari di lavoro, durata della fascia, giorni lavorativi, fuso orario, con quanti giorni di anticipo
  si può prenotare (`.env`) e l'elenco dei servizi con i prezzi (`config/services.json`).
- **Sicuro per progettazione:** i dati dei pulsanti vengono validati (un orario falsificato viene rifiutato), i nomi degli utenti sono
  sottoposti a escaping HTML, il token del bot non viene mai stampato, i dati personali restano fuori da git.

### Come funziona

```
/start ─► scelta servizio ─► scelta giorno ─► scelta orario libero ─► conferma
                                                                          │
                                          ┌───────────────────────────────┤
                                          ▼                               ▼
                           l'admin riceve una notifica       prenotazione salvata (SQLite)
                                                                          │
                                          promemoria N minuti prima ◄─────┘
```

### Stack

`Python 3.11+` · `aiogram 3` · `aiosqlite` · `asyncio` · `zoneinfo` · `pytest` + `pytest-asyncio` · `ruff` · GitHub Actions

### Avvio rapido

```bash
git clone https://github.com/sonoyumi/booking-bot.git
cd booking-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # impostare BOT_TOKEN (da @BotFather) e ADMIN_IDS
cp config/services.example.json config/services.json   # facoltativo: i propri servizi
booking-bot                   # oppure: python -m booking_bot
```

Test: `pytest` (33 test, incluso uno scenario end-to-end attraverso il vero Dispatcher di aiogram).

### Struttura del progetto

```
src/booking_bot/
├── schedule.py   # giorni lavorativi e fasce orarie: logica pura, senza Telegram
├── db.py         # archiviazione SQLite, protezione dalle doppie prenotazioni
├── handlers.py   # flusso di prenotazione, /my, /today
├── keyboards.py  # tastiere inline e callback data tipizzati
├── reminders.py  # attività di promemoria in background
├── services.py   # catalogo dei servizi da JSON
├── config.py     # impostazioni da .env
└── main.py       # assemblaggio dell'applicazione
```

### Autore

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)), sviluppatore Python: bot Telegram, web scraping, automazione.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)

> 💼 Ti serve un bot di prenotazione per la tua attività? Scrivimi.

### Licenza

MIT, vedi [LICENSE](LICENSE).

---

<a name="uk"></a>

## 🇺🇦 Українська

**[🇬🇧 English](#en)** · **[🇮🇹 Italiano](#it)** · **🇺🇦 Українська** · **[🇷🇺 Русский](#ru)**

Telegram-бот для запису клієнтів до салону, барбершопу, студії чи будь-якого малого бізнесу,
що працює за записом. Клієнт у кілька натискань обирає послугу, день і вільний час,
бот заздалегідь нагадує про візит, а власник отримує сповіщення про кожен новий запис і скасування.

### Можливості

- **Запис у 4 натискання:** послуга → день → вільний час → підтвердження. Минулі та зайняті слоти ніколи не показуються.
- **Жодних подвійних записів:** частковий UNIQUE-індекс у SQLite гарантує один активний запис на слот,
  навіть якщо два клієнти натиснуть «Підтвердити» одночасно.
- **«Мої записи»:** `/my` показує майбутні візити зі скасуванням в одне натискання; скасований час знову стає вільним.
- **Нагадування:** фонове завдання нагадує клієнту за N хвилин до візиту (один раз, навіть після перезапуску бота).
- **Для власника:** сповіщення про нові записи та скасування, `/today` — розклад на сьогодні.
- **Налаштовується без коду:** робочі години, тривалість слота, робочі дні, часовий пояс, на скільки днів уперед
  відкритий запис (`.env`) і список послуг із цінами (`config/services.json`).
- **Безпека:** дані кнопок перевіряються (підроблений час відхиляється), імена клієнтів екрануються,
  токен бота не потрапляє в логи, персональні дані не потрапляють у git.

### Як це працює

```
/start ─► вибір послуги ─► вибір дня ─► вибір вільного часу ─► підтвердження
                                                                        │
                                       ┌────────────────────────────────┤
                                       ▼                                ▼
                         адміну надходить сповіщення        запис збережено (SQLite)
                                                                        │
                                       нагадування за N хвилин ◄────────┘
```

### Стек

`Python 3.11+` · `aiogram 3` · `aiosqlite` · `asyncio` · `zoneinfo` · `pytest` + `pytest-asyncio` · `ruff` · GitHub Actions

### Швидкий старт

```bash
git clone https://github.com/sonoyumi/booking-bot.git
cd booking-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # вписати BOT_TOKEN (від @BotFather) і ADMIN_IDS
cp config/services.example.json config/services.json   # за бажанням: свої послуги
booking-bot                   # або: python -m booking_bot
```

Тести: `pytest` (33 тести, зокрема наскрізний сценарій через справжній Dispatcher aiogram).

### Структура проєкту

```
src/booking_bot/
├── schedule.py   # робочі дні та слоти: чиста логіка без Telegram
├── db.py         # зберігання в SQLite, захист від подвійного запису
├── handlers.py   # сценарій запису, /my, /today
├── keyboards.py  # inline-клавіатури й типізовані callback-дані
├── reminders.py  # фонові нагадування
├── services.py   # каталог послуг із JSON
├── config.py     # налаштування з .env
└── main.py       # збирання застосунку
```

### Автор

**Vladyslav Shokun** ([@sonoyumi](https://github.com/sonoyumi)) — Python-розробник: Telegram-боти, парсинг, автоматизація.

[![Telegram](https://img.shields.io/badge/Telegram-write%20me-2CA5E0?logo=telegram&logoColor=white)](https://t.me/sonoyumiii)
[![Email](https://img.shields.io/badge/Email-contact-EA4335?logo=gmail&logoColor=white)](mailto:sonoyumiii@gmail.com)

> 💼 Потрібен бот запису для вашого бізнесу? Напишіть мені.

### Ліцензія

MIT — див. [LICENSE](LICENSE).

---

<a name="ru"></a>

## 🇷🇺 Русский

**[🇬🇧 English](#en)** · **[🇮🇹 Italiano](#it)** · **[🇺🇦 Українська](#uk)** · **🇷🇺 Русский**

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
