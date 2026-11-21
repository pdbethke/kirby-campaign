"""Polities, the offices in them, and who held each office when.

A head of state is an ``Office`` whose scope is the polity itself; a reign is
a ``Tenure`` of that office. An election ends one tenure and begins the next,
and is recorded on the timeline.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_world import SourceRef, check_source_status

from kirby_campaign._checks import require_choice, require_order, require_text
from kirby_campaign.world_date import WorldDate

POLITY_KINDS = ("nation", "city_state", "territory", "other")
#: What an office is over: the whole polity, one locale, or one organisation.
SCOPE_KINDS = ("polity", "locale", "organisation")
#: How a tenure began.
TENURE_HOW = ("appointed", "elected", "succession", "seized", "founded", "other")


@dataclass(frozen=True, kw_only=True)
class Polity:
    id: str
    world_id: str
    name: str
    kind: str
    political_system: str | None
    active: bool
    capital_locale_id: str | None
    #: Locale ids (kirby-world). Who holds a place is a polity fact.
    territory: tuple[str, ...]
    color: int | None
    source_ref: SourceRef | None
    source_status: str | None

    def __post_init__(self) -> None:
        owner = f"polity {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id, name=self.name)
        require_choice(owner, "kind", self.kind, POLITY_KINDS)
        if self.capital_locale_id is not None and self.capital_locale_id not in self.territory:
            raise ValueError(f"{owner}: capital {self.capital_locale_id!r} is not in its territory")
        check_source_status(owner, self.source_ref is not None, self.source_status)


@dataclass(frozen=True, kw_only=True)
class Office:
    id: str
    world_id: str
    title: str
    polity_id: str
    scope_kind: str
    scope_id: str

    def __post_init__(self) -> None:
        owner = f"office {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id, title=self.title,
                     polity_id=self.polity_id, scope_id=self.scope_id)
        require_choice(owner, "scope_kind", self.scope_kind, SCOPE_KINDS)


@dataclass(frozen=True, kw_only=True)
class Tenure:
    id: str
    world_id: str
    office_id: str
    person_id: str
    started: WorldDate | None
    ended: WorldDate | None
    how: str

    def __post_init__(self) -> None:
        owner = f"tenure {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id, office_id=self.office_id,
                     person_id=self.person_id)
        require_choice(owner, "how", self.how, TENURE_HOW)
        require_order(owner, "started", self.started, "ended", self.ended)

    @property
    def is_open(self) -> bool:
        return self.ended is None
