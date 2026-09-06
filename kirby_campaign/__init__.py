"""kirby-campaign — the campaign entity layer's rules.

Teams, rosters, and the two-tier definition/instance merge. No database,
no HTTP, no tenancy: those stay in kirby-api, which maps its rows onto
these shapes.

**This package does not import kirby-combat, and kirby-combat does not
import it.** The bridge between a standing team and a fight's sides is a
plain string --- ``sides_from_teams`` returns ``{character_id: side}``,
and a combatant's ``side`` is a free ``str``. Typing ``side`` as a Team
reference would have made combat depend on the campaign layer, dragging
narrative prose and tenancy behind every fight.
"""
from kirby_campaign.team import (
    TEAM_TYPES, Team, TeamMember, assign_sides, sides_from_teams, teams_of,
)
from kirby_campaign.tiers import (
    TEAM_OVERRIDES, TEAM_STATE, effective, effective_team,
)

__all__ = [
    "TEAM_TYPES", "Team", "TeamMember",
    "sides_from_teams", "assign_sides", "teams_of",
    "effective", "effective_team", "TEAM_OVERRIDES", "TEAM_STATE",
]
