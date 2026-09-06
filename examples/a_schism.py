"""Rosters into sides — and the same roster split down the middle.

WHAT THIS SHOWS. A Team is an identity that persists between fights. A
`side` is an alignment within one fight. `sides_from_teams` is the DEFAULT
mapping from the first to the second, and `assign_sides` applies it
without ever overwriting a side someone already carries --- which is what
lets two teammates fight each other on Tuesday and still be teammates on
Wednesday, with no edit to the team.

Run twice below on ONE unchanged roster:

  1. Two teams, the obvious mapping: everyone fights for their team.
  2. A schism: three members are handed an explicit side first, and the
     team is left exactly as it was.

WHY THERE IS NO FIGHT HERE. This package does not import kirby-combat and
must not --- see `tests/test_independence.py`. It produces the plain
`{character_id: side}` mapping that a consumer feeds to the engine, and
stops there. Typing `side` as a Team reference would have made every
attack resolution depend on knowing what a campaign is.

THE TEAMS ARE INVENTED. Every real team in the corpus comes from CV1-CV3
(Champions Villains Volumes 1-3, with CV2 a volume dedicated to villain
teams) or Old School Enemies. Those entries ARE the books' prose --- paid
Hero Games material --- and this package is publishable, so no sourcebook
team appears in it.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from kirby_campaign import (
    Team,
    TeamMember,
    assign_sides,
    effective_team,
    sides_from_teams,
    teams_of,
)


@dataclass(frozen=True)
class Fighter:
    """Whatever a consumer's combatant is. Only `id` and `side` are read."""
    id: str
    side: str | None = None


SENTINELS = Team(
    id="sentinels", name="Sentinels of Dawn", team_type="hero",
    members=(
        TeamMember("aurora", "leader", 0),
        TeamMember("bulwark", "lieutenant", 1),
        TeamMember("cinder", "member", 2),
        TeamMember("dray", "member", 3),
    ),
    # A Base is a BUILD -- built with the base rules, HDC-imported, costed
    # by kirby-cost, and terrain with BODY and DEF once a fight reaches it.
    # Only the reference belongs here.
    base_ids=("dawn-spire",),
)

IRON_CHORUS = Team(
    id="iron-chorus", name="Iron Chorus", team_type="villain",
    members=(
        TeamMember("magnifex", "leader", 0),
        TeamMember("tolling", "member", 1),
        TeamMember("verdigris", "member", 2),
    ),
    base_ids=("the-foundry",),
)

ROSTER = [
    Fighter(i) for i in
    ("aurora", "bulwark", "cinder", "dray", "magnifex", "tolling", "verdigris")
]


def _show(title: str, fighters: list[Fighter]) -> None:
    print(f"\n  {title}")
    by_side: dict[str, list[str]] = {}
    for fighter in fighters:
        by_side.setdefault(fighter.side or f"solo:{fighter.id}", []).append(fighter.id)
    for side, ids in by_side.items():
        print(f"    {side:<18} {', '.join(sorted(ids))}")


def main() -> None:
    teams = [SENTINELS, IRON_CHORUS]

    print("ROSTERS INTO SIDES — no database, no fight engine.")
    for team in teams:
        leader = team.leader.character_id if team.leader else "(none)"
        print(f"\n  {team.name} ({team.team_type})")
        print(f"    roster : {', '.join(team.member_ids)}")
        print(f"    leader : {leader}")
        print(f"    bases  : {', '.join(team.base_ids) or '(none)'}")

    print(f"\n  sides_from_teams -> {sides_from_teams(teams)}")

    # ---- 1. The obvious mapping ----
    _show("Everyone fights for their team:", assign_sides(ROSTER, teams))

    # ---- 2. A schism, with the team untouched ----
    #
    # Three Sentinels are handed an explicit side BEFORE the mapping runs.
    # `assign_sides` leaves a side that is already set, because a per-fight
    # alignment is the more specific statement.
    loyalists = {"aurora", "cinder"}
    defectors = {"bulwark"}
    split = [
        replace(f, side="Loyalists") if f.id in loyalists
        else replace(f, side="Iron Chorus") if f.id in defectors
        else f
        for f in ROSTER
    ]
    _show("The same roster, split:", assign_sides(split, teams))

    print("\n  The team is unchanged by any of that:")
    print(f"    {SENTINELS.name} roster : {', '.join(SENTINELS.member_ids)}")
    print(f"    bulwark's teams        : "
          f"{[t.name for t in teams_of('bulwark', teams)]}")
    print("    -- still a Sentinel on paper, fighting for the Iron Chorus today.")

    # ---- The two-tier merge ----
    #
    # A campaign instance overlays its library definition: NULL inherits,
    # a set value wins, and instance-only state comes from the instance.
    definition = {
        "name": "Sentinels of Dawn", "team_type": "hero",
        "agenda": "Hold the line", "history": None,
        "tactics": "Massed ranged fire", "modus_operandi": None, "notes": None,
    }
    instance = {"name": "Sentinels of Dusk", "is_active": False,
                "status_notes": "disbanded after the schism"}
    merged = effective_team(definition, instance)

    print("\n  The same team as one campaign has it:")
    print(f"    name    : {merged['name']}   (overridden)")
    print(f"    agenda  : {merged['agenda']}   (inherited)")
    print(f"    active  : {merged['is_active']}   (instance-only state)")
    print(f"    notes   : {merged['status_notes']}")
    print("\n    `tactics` here is the team's PROSE, not kirby_combat.tactics —")
    print("    that one is the doctrine catalogue that picks a combatant's action.")


if __name__ == "__main__":
    main()
