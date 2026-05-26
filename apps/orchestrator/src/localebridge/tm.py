"""Translation memory: in-process key+locale -> translation lookup.

This is the test-friendly default. Production swaps in `store.SqlAlchemyTM`
(SQLAlchemy + Postgres) with the same shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Translation


@dataclass
class InMemoryTM:
    """Thread-unsafe (single-process) translation memory."""

    _store: dict[tuple[str, str], Translation] = field(default_factory=dict)

    def get(self, key: str, locale: str) -> Translation | None:
        return self._store.get((key, locale))

    def put(self, t: Translation) -> None:
        self._store[(t.key, t.locale)] = t

    def all_for_locale(self, locale: str) -> list[Translation]:
        return [t for (_k, loc), t in self._store.items() if loc == locale]

    def size(self) -> int:
        return len(self._store)
