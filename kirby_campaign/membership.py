"""Who belongs to which organisation, at what rank, and when.

A membership is a dated record, like a tenure. A promotion ends one
membership and starts another, so the history stays. A person may belong to
several organisations at once (a soldier who also informs for someone else),
but holds at most one open membership in any one of them.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_world import SourceRef, check_source_status

from kirby_campaign._checks import require_order, require_text
from kirby_campaign.world_date import WorldDate


@dataclass(frozen=True, kw_only=True)
class Membership:
    id: str
    world_id: str
    organisation_id: str
    #: May name someone the world no longer holds (a source pruned them).
    person_id: str
    #: A rank on the organisation's own ladder.
    rank: str
    started: WorldDate | None
    ended: WorldDate | None
    source_ref: SourceRef | None
    source_status: str | None

    def __post_init__(self) -> None:
        owner = f"membership {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id,
                     organisation_id=self.organisation_id, person_id=self.person_id,
                     rank=self.rank)
        require_order(owner, "started", self.started, "ended", self.ended)
        check_source_status(owner, self.source_ref is not None, self.source_status)

    @property
    def is_open(self) -> bool:
        return self.ended is None
