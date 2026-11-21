"""Organisations that act in the world, and the typed edges between things.

A ruling dynasty, a mob family and a villain organisation are the same
structure with a different ``kind``, each with its own rank ladder. An organisation may be backed by
several source families (one per country, for one that crosses borders) or
by none. A Team is something else: a group's identity for fights.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_world import SourceRef, check_source_status

from kirby_campaign._checks import require_choice, require_order, require_text
from kirby_campaign.world_date import WorldDate

ORGANISATION_KINDS = ("dynasty", "mob_family", "villain_org", "gang", "agency", "other")
#: What an EntityRef may point at.
ENTITY_KINDS = ("person", "organisation", "polity", "locale")
RELATION_KINDS = ("kin", "alliance", "war", "vassalage", "trade", "grudge", "debt")


@dataclass(frozen=True, kw_only=True)
class EntityRef:
    kind: str
    id: str

    def __post_init__(self) -> None:
        require_choice("entity ref", "kind", self.kind, ENTITY_KINDS)
        require_text("entity ref", id=self.id)


@dataclass(frozen=True, kw_only=True)
class Rank:
    """One rung of an organisation's ladder. Each organisation owns its ladder:
    a mob family's boss, underboss, lieutenant, soldier and associate, or a
    villain organisation's own."""

    name: str
    #: The HERO build (imported from HDC) members of this rank fight with when
    #: they have none of their own.
    archetype_character_id: str | None
    #: How hard a member of this rank is to hit, before strength is weighed.
    hit_failure_base: float
    #: How many members of lower rank guard a member of this rank.
    guards: int

    def __post_init__(self) -> None:
        require_text("rank", name=self.name)
        if not 0.0 <= self.hit_failure_base <= 1.0:
            raise ValueError(
                f"rank {self.name!r}: hit_failure_base must be 0-1, got {self.hit_failure_base}"
            )
        if self.guards < 0:
            raise ValueError(f"rank {self.name!r}: guards must be 0 or more, got {self.guards}")


@dataclass(frozen=True, kw_only=True)
class Organisation:
    id: str
    world_id: str
    name: str
    kind: str
    #: Highest first. Members and their ranks are ``Membership`` records.
    ranks: tuple[Rank, ...]
    head_id: str | None
    heir_id: str | None
    #: Locale ids (kirby-world): the organisation's turf.
    territory: tuple[str, ...]
    influence: float | None
    wealth: float | None
    source_refs: tuple[SourceRef, ...]
    source_status: str | None

    def __post_init__(self) -> None:
        owner = f"organisation {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id, name=self.name)
        require_choice(owner, "kind", self.kind, ORGANISATION_KINDS)
        if not self.ranks:
            raise ValueError(f"{owner}: needs at least one rank")
        names = [r.name for r in self.ranks]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            raise ValueError(f"{owner}: rank names used twice: {', '.join(dupes)}")
        if len(set(self.source_refs)) != len(self.source_refs):
            dupes = sorted({str(r) for r in self.source_refs if self.source_refs.count(r) > 1})
            raise ValueError(f"{owner}: source family listed twice: {', '.join(dupes)}")
        check_source_status(owner, bool(self.source_refs), self.source_status)

    def rank(self, name: str) -> Rank:
        for r in self.ranks:
            if r.name == name:
                return r
        raise KeyError(
            f"organisation {self.id!r} has no rank {name!r} (ladder: "
            f"{', '.join(r.name for r in self.ranks)})"
        )

    def rank_order(self, name: str) -> int:
        """0 is the highest rank."""
        return self.ranks.index(self.rank(name))


@dataclass(frozen=True, kw_only=True)
class Relation:
    id: str
    world_id: str
    kind: str
    a: EntityRef
    b: EntityRef
    since: WorldDate | None
    until: WorldDate | None
    cause_event_id: str | None

    def __post_init__(self) -> None:
        owner = f"relation {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id)
        require_choice(owner, "kind", self.kind, RELATION_KINDS)
        if self.a == self.b:
            raise ValueError(f"{owner}: an entity cannot have a relation with itself")
        require_order(owner, "since", self.since, "until", self.until)
