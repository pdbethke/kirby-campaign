"""A date in a campaign world's calendar.

Years may be zero or negative: a world's backstory (the births of the people
alive when it was made) can predate year 1. Only ordering is needed here, so
there is no calendar arithmetic; an importer converts its source's dates.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True, kw_only=True)
class WorldDate:
    year: int
    month: int
    day: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(f"WorldDate month must be 1-12, got {self.month}")
        if not 1 <= self.day <= 31:
            raise ValueError(f"WorldDate day must be 1-31, got {self.day}")

    def __str__(self) -> str:
        sign = "-" if self.year < 0 else ""
        return f"{sign}{abs(self.year):04d}-{self.month:02d}-{self.day:02d}"
