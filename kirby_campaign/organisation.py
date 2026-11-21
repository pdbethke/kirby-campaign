"""Organisations that act in the world, and the typed edges between things.

A ruling dynasty, a mob family and a villain organisation are the same
structure with a different ``kind``. An organisation may be backed by
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
class Organisation:
    id: str
    world_id: str
    name: str
    kind: str
    head_id: str | None
    heir_id: str | None
    #: Person ids. May name people the world no longer holds (pruned).
    member_ids: tuple[str, ...]
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
        for role in ("head_id", "heir_id"):
            person = getattr(self, role)
            if person is not None and person not in self.member_ids:
                raise ValueError(f"{owner}: {role} {person!r} is not one of its members")
        if len(set(self.source_refs)) != len(self.source_refs):
            dupes = sorted({str(r) for r in self.source_refs if self.source_refs.count(r) > 1})
            raise ValueError(f"{owner}: source family listed twice: {', '.join(dupes)}")
        check_source_status(owner, bool(self.source_refs), self.source_status)


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
