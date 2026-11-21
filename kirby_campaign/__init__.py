"""kirby-campaign — the campaign entity layer's rules.

Teams, rosters, and the two-tier definition/instance merge. No database,
no HTTP, no tenancy: those stay in kirby-api, which maps its rows onto
these shapes.

**This package imports kirby-combat; kirby-combat must never import
this one.** The direction is the design. kirby-campaign sits ABOVE the
engine: a Team becomes a ``Side``, and ``Side`` lives in the engine
because a free-for-all in an alley has sides and no campaign at all. The
reverse would make resolving an attack depend on knowing what a campaign
is, dragging rosters, narrative prose and eventually tenancy behind every
roll. ``tests/test_independence.py`` is what keeps that true.
"""
from kirby_campaign.campaign_layer import CampaignLayer, EncounterHook, visible_account
from kirby_campaign.membership import Membership
from kirby_campaign.organisation import (
    ENTITY_KINDS,
    ORGANISATION_KINDS,
    RELATION_KINDS,
    EntityRef,
    Organisation,
    Rank,
    Relation,
)
from kirby_campaign.person import Kin, Person
from kirby_campaign.polity import POLITY_KINDS, SCOPE_KINDS, TENURE_HOW, Office, Polity, Tenure
from kirby_campaign.rulings import RulingRecord, rulings_in_fight
from kirby_campaign.team import (
    TEAM_TYPES,
    Team,
    TeamMember,
    assign_sides,
    side_of_team,
    sides_from_teams,
    teams_of,
)
from kirby_campaign.tiers import (
    TEAM_OVERRIDES,
    TEAM_STATE,
    effective,
    effective_team,
)
from kirby_campaign.timeline import (
    CAUSE_KINDS,
    LAW_ORIGINS,
    LAW_STATUSES,
    PUBLIC,
    TRUTH,
    Cause,
    Law,
    WorldEvent,
    account_at,
)
from kirby_campaign.underworld import (
    DEFER,
    DROP,
    ROUTE_TO_SESSION,
    SEND,
    STEP_ACTIONS,
    STEP_STATUSES,
    Chain,
    ChainStep,
    UnderworldLimits,
    Verdict,
    validate_step,
)
from kirby_campaign.world_date import WorldDate
from kirby_campaign.world_state import WorldState

__all__ = [
    "CAUSE_KINDS",
    "DEFER",
    "DROP",
    "ENTITY_KINDS",
    "LAW_ORIGINS",
    "LAW_STATUSES",
    "ORGANISATION_KINDS",
    "POLITY_KINDS",
    "PUBLIC",
    "RELATION_KINDS",
    "ROUTE_TO_SESSION",
    "SCOPE_KINDS",
    "SEND",
    "STEP_ACTIONS",
    "STEP_STATUSES",
    "TEAM_OVERRIDES",
    "TEAM_STATE",
    "TEAM_TYPES",
    "TENURE_HOW",
    "TRUTH",
    "CampaignLayer",
    "Cause",
    "Chain",
    "ChainStep",
    "EncounterHook",
    "EntityRef",
    "Kin",
    "Law",
    "Membership",
    "Office",
    "Organisation",
    "Person",
    "Polity",
    "Rank",
    "Relation",
    "RulingRecord",
    "Team",
    "TeamMember",
    "Tenure",
    "UnderworldLimits",
    "Verdict",
    "WorldDate",
    "WorldEvent",
    "WorldState",
    "account_at",
    "assign_sides",
    "effective",
    "effective_team",
    "rulings_in_fight",
    "side_of_team",
    "sides_from_teams",
    "teams_of",
    "validate_step",
    "visible_account",
]
