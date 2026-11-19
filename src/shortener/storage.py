"""Storage layer: repository interface plus an in-memory implementation."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Protocol


@dataclass
class ShortUrl:
    code: str
    url: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    hits: int = 0


class UrlRepository(Protocol):
    def get(self, code: str) -> Optional[ShortUrl]: ...

    def add(self, item: ShortUrl) -> bool:
        """Insert item. Return False if the code already exists."""
        ...

    def increment_hits(self, code: str) -> None: ...


class InMemoryRepository:
    """Thread-safe dict-backed repository. Good for tests and local dev."""

    def __init__(self) -> None:
        self._items: dict[str, ShortUrl] = {}
        self._lock = threading.Lock()

    def get(self, code: str) -> Optional[ShortUrl]:
        with self._lock:
            return self._items.get(code)

    def add(self, item: ShortUrl) -> bool:
        with self._lock:
            if item.code in self._items:
                return False
            self._items[item.code] = item
            return True

    def increment_hits(self, code: str) -> None:
        with self._lock:
            if code in self._items:
                self._items[code].hits += 1
