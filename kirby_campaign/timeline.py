"""The world's timeline, its laws, and what each kind of reader may know.

Every event has a ``truth``. A secret event also has a ``public_account``:
what the street knows ("a body was pulled from the river"). There are two
tiers in this version: ``PUBLIC`` (every player) and ``TRUTH`` (the GM, and
any player the GM unlocks it for). An event with no public account is public:
everyone reads the truth.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_world import SourceRef

from kirby_campaign._checks import require_choice, require_order, require_text
from kirby_campaign.organisation import EntityRef
from kirby_campaign.world_date import WorldDate

#: What made an event happen: the world's source simulated it, an underworld
#: chain did it, a session's players did it, or the GM declared it.
CAUSE_KINDS = ("source", "chain", "session", "gm")
#: Causes that must name what caused them (a chain id, a session id).
_CAUSES_WITH_REF = ("chain", "session")

PUBLIC = 0
TRUTH = 1

LAW_ORIGINS = ("drafted", "gm")
LAW_STATUSES = ("in_force", "struck")


@dataclass(frozen=True, kw_only=True)
class Cause:
    kind: str
    ref: str | None

    def __post_init__(self) -> None:
        require_choice("cause", "kind", self.kind, CAUSE_KINDS)
        if self.kind in _CAUSES_WITH_REF and not self.ref:
            raise ValueError(f"a {self.kind} cause must name its {self.kind} (ref)")
        if self.kind not in _CAUSES_WITH_REF and self.ref is not None:
            raise ValueError(f"a {self.kind} cause takes no ref")


@dataclass(frozen=True, kw_only=True)
class WorldEvent:
    id: str
    world_id: str
    date: WorldDate
    #: Free text from whoever recorded it ("election_held", "hit").
    kind: str
    #: Person ids.
    actors: tuple[str, ...]
    #: Locale ids (kirby-world).
    places: tuple[str, ...]
    groups: tuple[EntityRef, ...]
    truth: str
    public_account: str | None
    cause: Cause
    source_ref: SourceRef | None

    def __post_init__(self) -> None:
        require_text(f"event {self.id!r}", id=self.id, world_id=self.world_id,
                     kind=self.kind, truth=self.truth)


def account_at(event: WorldEvent, tier: int) -> str:
    """The account of ``event`` a reader at ``tier`` sees."""
    if tier == TRUTH:
        return event.truth
    if tier == PUBLIC:
        return event.truth if event.public_account is None else event.public_account
    raise ValueError(f"knowledge tier {tier} is not PUBLIC ({PUBLIC}) or TRUTH ({TRUTH})")


@dataclass(frozen=True, kw_only=True)
class Law:
    id: str
    world_id: str
    polity_id: str
    title: str
    text: str
    enacted: WorldDate
    repealed: WorldDate | None
    cause_event_id: str | None
    #: ``drafted`` laws come from the world's events; ``gm`` laws were written
    #: by the GM. A drafted law is in force unless the GM strikes it.
    origin: str
    status: str

    def __post_init__(self) -> None:
        owner = f"law {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id, polity_id=self.polity_id,
                     title=self.title, text=self.text)
        require_choice(owner, "origin", self.origin, LAW_ORIGINS)
        require_choice(owner, "status", self.status, LAW_STATUSES)
        require_order(owner, "enacted", self.enacted, "repealed", self.repealed)
