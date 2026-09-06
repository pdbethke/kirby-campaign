"""Team — a named, standing group of characters. The Avengers.

WHAT WAS ALREADY BUILT, AND WHERE. kirby-api has a full team system:
``TeamDef`` (the definition), ``TeamMemberDef`` (roster rows, carrying a
``role`` of leader / lieutenant / member and a ``sort_order``),
``TeamInstance`` (a campaign-scoped overlay of a def) and ``TeamPage``,
under an architecture spec (``2026-05-29-kirby-entity-layer-design.md``)
that makes Team the single canonical group concept. This module is the
RULES half of that, carved out on 2026-09-06. It is not a new idea and
deliberately not a second one --- building a parallel team concept while
``TeamDef`` stood would repeat the duplicate-Darkness mistake.

WHY TEAM IS FIRST-CLASS AT ALL: **villain teams**. The entity layer was
brainstormed while scoping the *Old School Enemies* import, and villain
teams were the gap the bestiary could not express. The corpus already
carries the sources --- CV1, CV2 and CV3 (Champions Villains Volumes 1-3)
plus OSE --- and **CV2 is a volume dedicated to them**. A team entry in
those books carries its *tactics, its roster, and its base*, which is why
this shape carries all three.

TEAM IS NOT SIDE, AND CONFLATING THEM IS THE TRAP. A Team is an identity
that persists between fights --- you are an Avenger on Tuesday and still
one on Wednesday. A ``side`` is an alignment within ONE fight: who is
shooting at whom right now. They usually agree, and they must be able to
disagree:

* Two Avengers on opposite sides of a training bout, or a schism.
* An Avenger and a villain temporarily allied against something worse.
* A mind-controlled Avenger fighting their own team --- which kirby-api
  already models by widening the target set when the control degree
  reaches "contrary".

So ``sides_from_teams`` is the DEFAULT mapping from standing identity to
this fight's alignment, not an identity between the two. A caller who
wants Civil War overrides the side and keeps the Team.

Measured 2026-09-06: nothing under ``kirby/combat/`` in the parked driver
ever read ``TeamMemberDef`` or ``team_member_def``. The link from "the
Avengers" to "who is on my side in this fight" did not exist in code at
all --- sides were set by hand, per fight. This module is that link.

WHAT MOVED AND WHAT DID NOT. ``TeamDef`` carries twenty columns. Three
describe the group as a fight or a roster sees it --- ``name``,
``team_type``, and its members --- and those are here, with the HQ edge.
The rest are storage and retrieval concerns and stay in kirby-api:
``tenant_id`` and ``owner_id``, ``embedding`` and ``codex_chunk_id``, the
narrative prose (``agenda`` / ``history`` / ``tactics`` /
``modus_operandi`` / ``notes``), the ``real_history_*`` set, and the
timestamps.

**A NAME COLLISION, STATED RATHER THAN DISCOVERED LATER.**
``TeamDef.tactics`` is a paragraph a GM or a sourcebook wrote about how a
team fights. ``kirby_combat.tactics`` is the doctrine catalogue --- code
that decides what a combatant does this Phase. They are unrelated. This
module holds neither: the prose stays in kirby-api, the catalogue stays
in kirby-combat.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

#: The team kinds kirby-api's ``team_def.team_type`` CHECK constraint
#: allows, copied verbatim so the two cannot drift. "neutral" and "other"
#: are as legal as "hero" --- an agency or a faction is a team.
TEAM_TYPES = ("hero", "villain", "agency", "neutral", "other")


@dataclass(frozen=True)
class TeamMember:
    """One character's membership in a team.

    ``role`` mirrors ``team_member_def.role`` (leader / lieutenant /
    member / ...). NO RULE READS IT --- measured across kirby-combat and
    the parked driver on 2026-09-06 --- so it is carried as data rather
    than given a meaning the books do not give it. Coordinated Attacks
    are the likely first caller. ``sort_order`` is the roster's display
    order, likewise carried and not interpreted.
    """

    character_id: str
    role: str | None = None
    sort_order: int = 0


@dataclass(frozen=True)
class Team:
    """A named group of characters that exists between fights.

    ``base_ids`` are OPAQUE identifiers this module never dereferences ---
    the entity spec's ``team_base_def`` join, which records a team's
    canonical HQ(s). The edge is in scope because a team entry in the
    books IS its tactics, its roster and its base, and dropping the link
    would discard a relationship the source hands over for free.

    THE BASE ITSELF IS A BUILD, WHICH IS WHY THIS IS ONLY AN ID. A Base is
    built with the base-building rules and imported from HDC, the same as
    a character: kirby-cost costs it, and in a fight its walls and doors
    are terrain with BODY and DEF. It is not campaign narrative, so it
    does not belong in this module in any form richer than a reference.
    Holding a real Base here would drag the build engine behind every
    roster query and put structural rules in the entity layer --- the
    same error as putting the turn loop in a web service. The engine
    treatment is entity-agnostic on purpose: a base, a vehicle and a
    turret are all builds.
    """

    id: str
    name: str
    team_type: str = "other"
    members: tuple[TeamMember, ...] = ()
    base_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.team_type not in TEAM_TYPES:
            raise ValueError(
                f"team_type {self.team_type!r} is not one of {TEAM_TYPES}"
            )
        if not (self.name or "").strip():
            raise ValueError("a team needs a name; `side` is reported by name")
        seen: set[str] = set()
        for member in self.members:
            if member.character_id in seen:
                raise ValueError(
                    f"{self.name!r} lists {member.character_id!r} twice; a "
                    f"character is on a team once or not at all"
                )
            seen.add(member.character_id)

    @property
    def roster(self) -> tuple[TeamMember, ...]:
        """Members in roster order (``sort_order``, then id for stability)."""
        return tuple(
            sorted(self.members, key=lambda m: (m.sort_order, m.character_id))
        )

    @property
    def member_ids(self) -> tuple[str, ...]:
        return tuple(m.character_id for m in self.roster)

    @property
    def leader(self) -> TeamMember | None:
        """The member whose role is "leader", or ``None``.

        A team may have no leader (a loose faction) and this returns the
        FIRST in roster order if somehow several are marked, rather than
        raising --- a sourcebook with two leaders is a data quirk, not a
        reason to refuse to run a fight.
        """
        for member in self.roster:
            if (member.role or "").casefold() == "leader":
                return member
        return None

    def __contains__(self, character_id: object) -> bool:
        return any(m.character_id == character_id for m in self.members)

    def with_member(self, member: TeamMember) -> Team:
        """A new Team with ``member`` added. Immutable, like everything here."""
        return replace(self, members=(*self.members, member))

    def without_member(self, character_id: str) -> Team:
        return replace(
            self,
            members=tuple(m for m in self.members if m.character_id != character_id),
        )


def sides_from_teams(teams: Iterable[Team]) -> dict[str, str]:
    """Map each member to their team's name --- the default fight alignment.

    The result is exactly what a combatant's ``side`` wants: a free string
    per character. Team NAME rather than id, because ``side`` is what gets
    reported back as the winner and "Avengers" reads better than a UUID.
    ``kirby_combat.loop.validate_sides`` will catch two teams whose names
    differ only in case before that can quietly become two armies.

    A character on two teams RAISES rather than silently taking the last
    one, since which side they fight for would otherwise depend on
    iteration order. Real crossovers happen; the caller resolves them by
    setting that character's side for that fight --- which is the whole
    reason side and team are separate things.
    """
    sides: dict[str, str] = {}
    conflicts: dict[str, set[str]] = {}
    for team in teams:
        for member_id in team.member_ids:
            previous = sides.get(member_id)
            if previous is not None and previous != team.name:
                conflicts.setdefault(member_id, {previous}).add(team.name)
            sides[member_id] = team.name
    if conflicts:
        detail = "; ".join(
            f"{cid!r} on {sorted(names)}" for cid, names in sorted(conflicts.items())
        )
        raise ValueError(
            f"a character cannot start a fight on two sides: {detail}. "
            f"Set their side explicitly for this fight instead."
        )
    return sides


def assign_sides(combatants: Iterable, teams: Iterable[Team], *, overwrite: bool = False):
    """Return the combatants with ``side`` filled in from their team.

    A combatant who already carries a ``side`` KEEPS it unless
    ``overwrite=True``: an explicit per-fight alignment is the more
    specific statement and outranks standing membership, which is what
    makes a schism or a mind-controlled turncoat expressible without
    editing the team.

    A combatant on no team is left alone, so they remain their own side
    --- a bystander in a war between named teams is not on one of them.

    Takes any object with an ``id`` and a ``side`` field. Typed loosely on
    purpose: this module must not import kirby-combat, and does not.
    """
    by_character = sides_from_teams(teams)
    out = []
    for combatant in combatants:
        side = by_character.get(combatant.id)
        if side is None or (getattr(combatant, "side", None) and not overwrite):
            out.append(combatant)
        else:
            out.append(replace(combatant, side=side))
    return out


def teams_of(character_id: str, teams: Iterable[Team]) -> tuple[Team, ...]:
    """Every team the character is on, in the order given.

    Plural deliberately: membership in several teams is legal as a
    standing fact (a character can be an Avenger and a Defender). It is
    only ambiguous when a FIGHT needs one side, which is where
    ``sides_from_teams`` raises.
    """
    return tuple(team for team in teams if character_id in team)
