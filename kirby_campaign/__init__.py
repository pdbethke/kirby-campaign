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
from kirby_campaign.world_date import WorldDate

__all__ = [
    "POLITY_KINDS",
    "SCOPE_KINDS",
    "TEAM_OVERRIDES",
    "TEAM_STATE",
    "TEAM_TYPES",
    "TENURE_HOW",
    "Kin",
    "Office",
    "Person",
    "Polity",
    "RulingRecord",
    "Team",
    "TeamMember",
    "Tenure",
    "WorldDate",
    "assign_sides",
    "effective",
    "effective_team",
    "rulings_in_fight",
    "side_of_team",
    "sides_from_teams",
    "teams_of",
]
