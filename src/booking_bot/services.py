"""Catalog of services loaded from a JSON file."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# The id travels inside Telegram callback data (64-byte limit, ":" is the separator).
_ID_RE = re.compile(r"^[a-z0-9_-]{1,24}$")


@dataclass(frozen=True)
class Service:
    id: str
    title: str
    price: str = ""

    @property
    def label(self) -> str:
        return f"{self.title} · {self.price}" if self.price else self.title


def load_services(path: Path) -> dict[str, Service]:
    """Reads the catalog; falls back to services.example.json so the demo works out of the box."""
    if not path.exists():
        example = path.with_name("services.example.json")
        logger.warning("%s not found, using %s", path.name, example.name)
        path = example

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError(f"{path}: expected a non-empty JSON list of services")

    services: dict[str, Service] = {}
    for item in data:
        service = Service(id=str(item["id"]), title=str(item["title"]), price=str(item.get("price", "")))
        if not _ID_RE.match(service.id):
            raise ValueError(f"{path}: invalid service id {service.id!r} (use a-z, 0-9, _ and -)")
        if service.id in services:
            raise ValueError(f"{path}: duplicate service id {service.id!r}")
        services[service.id] = service
    return services


def service_title(services: dict[str, Service], service_id: str) -> str:
    """Title for display; falls back to the id if the service was removed from the catalog."""
    service = services.get(service_id)
    return service.title if service else service_id
