"""The underworld: chains of moves between organisations, run unattended
inside limits the GM sets for each world.

A planner (outside this package) proposes chains: one family hits another's
lieutenant, the other answers, and so on. Every step is validated here,
with pure rules, before anything acts on it. A step against a player
character is never sent and never dropped: it becomes an encounter for that
character's next session.
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_campaign._checks import require_choice, require_text
from kirby_campaign.organisation import EntityRef
from kirby_campaign.world_state import WorldState

STEP_ACTIONS = ("hit", "claim_turf")
STEP_STATUSES = ("planned", "done", "failed", "waiting_on_session", "dropped", "deferred")
#: What each action may target.
_TARGET_KIND = {"hit": "person", "claim_turf": "locale"}

SEND = "send"
ROUTE_TO_SESSION = "route_to_session"
DEFER = "defer"
DROP = "drop"


@dataclass(frozen=True, kw_only=True)
class UnderworldLimits:
    """A world's limits. No defaults: a world has none until the GM sets them,
    and its underworld does not run without them."""

    world_id: str
    #: The most hits sent in one week, across all chains. Steps over the cap wait.
    max_hits_per_week: int
    protected_person_ids: frozenset[str]
    #: Anyone holding one of these offices is protected while they hold it.
    protected_office_ids: frozenset[str]

    def __post_init__(self) -> None:
        require_text("underworld limits", world_id=self.world_id)
        if self.max_hits_per_week < 0:
            raise ValueError(
                f"underworld limits: max_hits_per_week must be 0 or more, got {self.max_hits_per_week}"
            )


@dataclass(frozen=True, kw_only=True)
class ChainStep:
    id: str
    actor_org_id: str
    action: str
    target: EntityRef
    #: Exactly one motive: a relation (a grudge), an event, or an earlier step.
    motive_relation_id: str | None
    motive_event_id: str | None
    motive_step_id: str | None
    status: str

    def __post_init__(self) -> None:
        owner = f"chain step {self.id!r}"
        require_text(owner, id=self.id, actor_org_id=self.actor_org_id)
        require_choice(owner, "action", self.action, STEP_ACTIONS)
        require_choice(owner, "status", self.status, STEP_STATUSES)
        motives = [m for m in (self.motive_relation_id, self.motive_event_id,
                               self.motive_step_id) if m is not None]
        if len(motives) != 1:
            raise ValueError(f"{owner}: needs exactly one motive, has {len(motives)}")
        if self.target.kind != _TARGET_KIND[self.action]:
            raise ValueError(
                f"{owner}: a {self.action} targets a {_TARGET_KIND[self.action]}, "
                f"not a {self.target.kind}"
            )


@dataclass(frozen=True, kw_only=True)
class Chain:
    id: str
    world_id: str
    steps: tuple[ChainStep, ...]

    def __post_init__(self) -> None:
        owner = f"chain {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id)
        seen: set[str] = set()
        for i, step in enumerate(self.steps):
            if step.id in seen:
                raise ValueError(f"{owner}: step id {step.id!r} is used twice")
            if step.motive_step_id is not None:
                if i == 0:
                    raise ValueError(
                        f"{owner}: the first step cites step {step.motive_step_id!r}; a feud "
                        "starts from a relation or an event in the world"
                    )
                if step.motive_step_id not in seen:
                    raise ValueError(
                        f"{owner}: step {step.id!r} answers {step.motive_step_id!r}, which is "
                        "not an earlier step of this chain"
                    )
            seen.add(step.id)


@dataclass(frozen=True, kw_only=True)
class Verdict:
    outcome: str
    reason: str
    #: Set only for ``route_to_session``: whose session the encounter goes to.
    campaign_id: str | None


def _verdict(outcome: str, reason: str, campaign_id: str | None = None) -> Verdict:
    return Verdict(outcome=outcome, reason=reason, campaign_id=campaign_id)


#: What an answering step does while the step it answers has not happened.
_WAIT_ON = ("planned", "deferred", "waiting_on_session")


def _answered_step_verdict(step: ChainStep, chain: Chain) -> Verdict | None:
    """A step that answers an earlier one waits until that step happened, and
    dies with it if it never will."""
    if step.motive_step_id is None:
        return None
    cited = next(s for s in chain.steps if s.id == step.motive_step_id)
    if cited.status in _WAIT_ON:
        return _verdict(DEFER, f"the step it answers, {cited.id!r}, has not happened yet")
    if cited.status != "done":
        return _verdict(DROP, f"the step it answers, {cited.id!r}, was {cited.status}")
    return None


def validate_step(step: ChainStep, *, chain: Chain, state: WorldState,
                  limits: UnderworldLimits | None, hits_sent_this_week: int) -> Verdict:
    """Decide what happens to one planned step of ``chain``. Checks run in a
    fixed order; the first that applies decides.

    A world, chain or set of limits that does not match is a caller error and
    raises; everything about the step itself is a verdict."""
    if step not in chain.steps:
        raise ValueError(f"step {step.id!r} is not a step of chain {chain.id!r}")
    if chain.world_id != state.world_id:
        raise ValueError(f"chain {chain.id!r} is in world {chain.world_id!r}, not {state.world_id!r}")
    if limits is None:
        return _verdict(DROP, f"world {state.world_id!r} has no underworld limits set")
    if limits.world_id != state.world_id:
        raise ValueError(
            f"the underworld limits are for world {limits.world_id!r}, not {state.world_id!r}"
        )
    try:
        actor = state.organisation(step.actor_org_id)
    except KeyError:
        return _verdict(DROP, f"actor organisation {step.actor_org_id!r} is not in the world")
    if actor.source_status == "gone":
        return _verdict(DROP, f"actor organisation {step.actor_org_id!r} is gone from the source")
    for kind, cited, lookup in (("relation", step.motive_relation_id, state.relation),
                                ("event", step.motive_event_id, state.event)):
        if cited is not None:
            try:
                lookup(cited)
            except KeyError:
                return _verdict(DROP, f"the cited {kind} {cited!r} is not in the world")
    if step.action != "hit":
        # Turf targets are locale ids, which live in kirby-world's Atlas; the
        # caller that holds the Atlas checks them.
        waiting = _answered_step_verdict(step, chain)
        if waiting is not None:
            return waiting
        return _verdict(SEND, "turf claim; locale checked against the atlas by the caller")
    target_id = step.target.id
    if not state.has_person(target_id):
        return _verdict(DROP, f"target {target_id!r} is not in the world")
    target = state.person(target_id)
    if target.source_status == "gone":
        return _verdict(DROP, f"target {target_id!r} is gone from the world's source")
    if not target.alive:
        return _verdict(DROP, f"target {target_id!r} is already dead")
    if target_id in limits.protected_person_ids:
        return _verdict(DROP, f"target {target_id!r} is protected")
    for office in state.offices_held_by(target_id):
        if office.id in limits.protected_office_ids:
            return _verdict(DROP, f"target {target_id!r} holds protected office {office.id!r}")
    # A target that can never be hit is dropped now; only then does the step
    # wait for (or die with) the step it answers.
    waiting = _answered_step_verdict(step, chain)
    if waiting is not None:
        return waiting
    if target.pc:
        return _verdict(ROUTE_TO_SESSION, f"target {target_id!r} is a player character",
                        campaign_id=target.campaign_id)
    if hits_sent_this_week >= limits.max_hits_per_week:
        return _verdict(DEFER, f"this week's {limits.max_hits_per_week} hits are spent")
    return _verdict(SEND, "valid")
