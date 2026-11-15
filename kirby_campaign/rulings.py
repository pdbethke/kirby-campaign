"""GM rulings as a campaign stores them, and as one fight is handed them.

A campaign keeps a RULING RECORD per sentence the GM wrote: whose character,
which power (or None for the body), the closed fact, and his own words. The
engine's `kirby_combat.rulings.Ruling` is the shape a fight reads. This module
is the one place a stored record becomes an engine ruling, so kirby-api maps
its rows onto `RulingRecord` and never re-implements the selection.

WHY HERE AND NOT IN THE ENGINE. A record knows its campaign and its author;
the engine must not (a fight in an alley has no campaign). Same direction as
`team.py`: this package imports the engine, never the reverse.

No defaults, no coercion: the engine's `Ruling` validates the fact against
its closed vocabulary, so an unknown fact raises ValueError here rather than
reaching a fight as an unread string.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from kirby_combat.rulings import Ruling


@dataclass(frozen=True)
class RulingRecord:
    """One stored ruling. ``power_id`` None is a fact about the character's
    body (a `BodyFact` value); otherwise the HD ID of one of his powers and
    the fact is a `DeliveryRoute` value."""

    campaign_id: str
    character_id: str
    power_id: str | None
    fact: str
    sentence: str
    author_id: str


def rulings_in_fight(
    records: Iterable[RulingRecord], *, campaign_id: str, character_id: str,
) -> tuple[Ruling, ...]:
    """The engine rulings that apply to one character in one campaign.

    Only that campaign's and that character's records count: rulings are a
    table's, never shared across campaigns. Order is stable by
    ``(power_id or "", fact)`` so a replay folds the same rows the same way
    whatever order the database returned them in.
    """
    mine = [r for r in records
            if r.campaign_id == campaign_id and r.character_id == character_id]
    mine.sort(key=lambda r: (r.power_id or "", r.fact))
    return tuple(Ruling(r.power_id, r.fact, r.sentence) for r in mine)
