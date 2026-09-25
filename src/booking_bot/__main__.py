"""Entry points: `python -m booking_bot` or the `booking-bot` command."""

import asyncio
import contextlib

from booking_bot.main import main


def run() -> None:
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())


if __name__ == "__main__":
    run()
