"""Hits: who is sent, who guards the target, how a hit resolves without a
fight, and what follows from any hit.

A hit is normally fought, off-screen, by the combat engine (the consumer's
runner does that; this package does not import it). Everything here is pure:
picking the two sides, the fallback odds for an organisation with no builds
to fight with, and turning a result into deaths, an event and a grudge.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_campaign.membership import Membership
from kirby_campaign.underworld import ChainStep
from kirby_campaign.world_state import WorldState


@dataclass(frozen=True, kw_only=True)
class Squad:
    """The two sides of a hit. ``defenders`` starts with the target."""

    attackers: tuple[str, ...]
    defenders: tuple[str, ...]
    target_id: str
    attacker_org_id: str
    #: The organisation the target belongs to; None for an outsider.
    defender_org_id: str | None


def _available(state: WorldState, person_id: str) -> bool:
    if not state.has_person(person_id):
        return False
    p = state.person(person_id)
    return p.alive and p.source_status != "gone"


def _side_of(state: WorldState, person_id: str) -> Membership | None:
    """The membership in which the person holds their highest rank (ties: the
    lowest organisation id)."""
    best = None
    for ms in state.memberships_of(person_id):
        key = (state.organisation(ms.organisation_id).rank_order(ms.rank), ms.organisation_id)
        if best is None or key < best[0]:
            best = (key, ms)
    return None if best is None else best[1]


def select_hit_squad(step: ChainStep, *, state: WorldState) -> Squad:
    if step.action != "hit":
        raise ValueError(f"chain step {step.id!r} is a {step.action}, not a hit")
    target_id = step.target.id
    side = _side_of(state, target_id)
    defenders = [target_id]
    if side is not None:
        org = state.organisation(side.organisation_id)
        guards = org.rank(side.rank).guards
        below = [ms for ms in state.members_of(org.id, rank=None)
                 if org.rank_order(ms.rank) > org.rank_order(side.rank)
                 and _available(state, ms.person_id)]
        defenders += [ms.person_id for ms in below[:guards]]
    attacker = state.organisation(step.actor_org_id)
    defending_members = (
        set() if side is None
        else {ms.person_id for ms in state.members_of(side.organisation_id, rank=None)}
    )
    # Lowest rank first (bosses do not do their own hits), then by person id.
    # Nobody who also belongs to the target's organisation is sent against it.
    pool = sorted(
        (ms for ms in state.members_of(attacker.id, rank=None)
         if _available(state, ms.person_id)
         and ms.person_id not in defenders and ms.person_id not in defending_members),
        key=lambda ms: (-attacker.rank_order(ms.rank), ms.person_id),
    )
    pool = [ms.person_id for ms in pool]
    others = [pid for pid in pool if pid != attacker.head_id]
    chosen = others[:len(defenders)] if others else pool[:1]
    return Squad(attackers=tuple(chosen), defenders=tuple(defenders), target_id=target_id,
                 attacker_org_id=attacker.id,
                 defender_org_id=None if side is None else side.organisation_id)
