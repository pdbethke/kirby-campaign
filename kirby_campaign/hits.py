"""Hits: who is sent, who guards the target, how a hit resolves without a
fight, and what follows from any hit.

A hit is normally fought, off-screen, by the combat engine (the consumer's
runner does that; this package does not import it). Everything here is pure:
picking the two sides, the fallback odds for an organisation with no builds
to fight with, and turning a result into deaths, an event and a grudge.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_campaign._checks import require_choice
from kirby_campaign.membership import Membership
from kirby_campaign.underworld import ChainStep, UnderworldLimits
from kirby_campaign.world_state import WorldState

#: The highest failure chance the fallback gives (spec §6.7a).
FAILURE_CAP = 0.95
HIT_HOWS = ("fight", "odds")


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


@dataclass(frozen=True, kw_only=True)
class HitResult:
    """What happened in a hit, however it was resolved."""

    target_killed: bool
    #: Everyone who died, on either side.
    casualties: tuple[str, ...]
    #: Defenders who lived and saw who came for them.
    survivors_who_saw: tuple[str, ...]
    #: Whether the street learned who did it.
    leaked: bool
    how: str

    def __post_init__(self) -> None:
        require_choice("hit result", "how", self.how, HIT_HOWS)


def _strength(state: WorldState, org_id: str) -> float:
    org = state.organisation(org_id)
    if org.influence is None or org.influence <= 0:
        raise ValueError(
            f"organisation {org_id!r} has no strength (influence {org.influence!r}); "
            "a hit by odds needs both sides' influence"
        )
    return org.influence


def failure_chance(step: ChainStep, *, state: WorldState, limits: UnderworldLimits) -> float:
    """The fallback's chance that a hit fails: the target's rank base, scaled by
    the defending organisation's strength against the attacker's, capped."""
    side = _side_of(state, step.target.id)
    if side is None:
        return limits.outsider_failure_base
    org = state.organisation(side.organisation_id)
    base = org.rank(side.rank).hit_failure_base
    attacker = _strength(state, step.actor_org_id)
    defender = _strength(state, org.id)
    return min(FAILURE_CAP, base * 2 * defender / (attacker + defender))


def resolve_hit_by_odds(step: ChainStep, *, state: WorldState, limits: UnderworldLimits,
                        roll: float, leak_roll: float) -> HitResult:
    """Resolve a hit without a fight. The caller draws both rolls (in [0, 1))
    and records them, so the outcome can be replayed."""
    for name, value in (("roll", roll), ("leak_roll", leak_roll)):
        if not 0.0 <= value < 1.0:
            raise ValueError(f"{name} must be in [0, 1), got {value}")
    target = step.target.id
    if roll < failure_chance(step, state=state, limits=limits):
        return HitResult(target_killed=False, casualties=(), survivors_who_saw=(target,),
                         leaked=leak_roll < limits.leak_chance, how="odds")
    return HitResult(target_killed=True, casualties=(target,), survivors_who_saw=(),
                     leaked=False, how="odds")
