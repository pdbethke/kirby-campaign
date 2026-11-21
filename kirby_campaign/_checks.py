"""Validation shared by the world records. Private: the rules, not an API."""
from __future__ import annotations

from collections.abc import Iterable


def require_text(owner: str, **values: object) -> None:
    for field, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{owner}: {field} is required")


def require_choice(owner: str, field: str, value: object, allowed: Iterable[str]) -> None:
    allowed = tuple(allowed)
    if value not in allowed:
        raise ValueError(f"{owner}: {field} {value!r} is not one of {allowed}")


def require_order(owner: str, first_name: str, first, second_name: str, second) -> None:
    """``second`` may not come before ``first`` when both are known."""
    if first is not None and second is not None and second < first:
        raise ValueError(f"{owner}: {second_name} {second} is before {first_name} {first}")
