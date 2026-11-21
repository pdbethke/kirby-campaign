"""A city of rival families: the world model, built by hand.

Harbour City has an elected mayor, three mob families with turf in different
districts, and a villain organisation with a nest in the docks. One family
holds a grudge against another, and the underworld plans a short feud. Each
planned step is validated against the world and the GM's limits.

Uses kirby-world (the geography) and kirby-campaign (everything else) only.
Every name is invented.
"""
from dataclasses import replace

from kirby_world import Atlas, Locale

from kirby_campaign import (
    Chain,
    ChainStep,
    EntityRef,
    Kin,
    Office,
    Organisation,
    Person,
    Polity,
    Rank,
    Relation,
    Tenure,
    UnderworldLimits,
    WorldDate,
    WorldState,
    validate_step,
)

W = "harbour"
NO_KIN = Kin(spouse_ids=(), parent_ids=(), child_ids=())


def district(id, name, parent):
    return Locale(id=id, world_id=W, parent_locale_id=parent, name=name, kind="district",
                  center=None, terrain=None, scene_ids=(), source_ref=None, source_status=None)


atlas = Atlas(world_id=W, world_map=None, regions=(), locales=(
    Locale(id="city", world_id=W, parent_locale_id=None, name="Harbour City", kind="town",
           center=None, terrain=None, scene_ids=(), source_ref=None, source_status=None),
    district("old-quarter", "The Old Quarter", "city"),
    district("the-docks", "The Docks", "city"),
    district("hilltop", "Hilltop", "city"),
))


def npc(id, name, **over):
    fields = {"id": id, "world_id": W, "names": {"English": name}, "gender": None,
              "born": None, "died": None, "polity_id": "harbour-city", "culture": None,
              "religion": None, "traits": (), "skills": {}, "kin": NO_KIN,
              "character_id": None, "pc": False, "campaign_id": None, "source_ref": None,
              "source_status": None}
    fields.update(over)
    return Person(**fields)


LADDER = (Rank(name="boss", archetype_character_id=None, hit_failure_base=0.4, guards=2),
          Rank(name="lieutenant", archetype_character_id=None, hit_failure_base=0.2, guards=1),
          Rank(name="soldier", archetype_character_id=None, hit_failure_base=0.1, guards=0))


def family(id, name, kind, head, turf):
    return Organisation(id=id, world_id=W, name=name, kind=kind, ranks=LADDER, head_id=head,
                        heir_id=None, territory=turf, influence=50.0, wealth=None,
                        source_refs=(), source_status=None)


state = WorldState(
    world_id=W,
    polities=(Polity(id="harbour-city", world_id=W, name="Harbour City", kind="city_state",
                     political_system="Republic", active=True, capital_locale_id="city",
                     territory=tuple(loc.id for loc in atlas.locales), color=None,
                     source_ref=None, source_status=None),),
    offices=(Office(id="mayor", world_id=W, title="Mayor", polity_id="harbour-city",
                    scope_kind="polity", scope_id="harbour-city"),),
    tenures=(Tenure(id="t-1", world_id=W, office_id="mayor", person_id="iris",
                    started=WorldDate(year=1931, month=1, day=1), ended=None, how="elected"),),
    people=(npc("iris", "Iris Calloway"), npc("sal", "Sal Brenner"), npc("rook", "Rook Talley"),
            npc("vera", "Vera Okafor"), npc("coilmaster", "The Coilmaster"),
            npc("ada", "Ada Varga", pc=True, campaign_id="tuesday-group")),
    organisations=(family("brenners", "The Brenner Family", "mob_family", "sal", ("old-quarter",)),
                   family("talleys", "The Talley Outfit", "mob_family", "rook", ("the-docks",)),
                   family("okafors", "The Okafor Crew", "mob_family", "vera", ("hilltop",)),
                   family("coil", "The Coil", "villain_org", "coilmaster", ("the-docks",))),
    relations=(Relation(id="grudge", world_id=W, kind="grudge",
                        a=EntityRef(kind="organisation", id="talleys"),
                        b=EntityRef(kind="organisation", id="brenners"),
                        since=WorldDate(year=1930, month=4, day=1), until=None,
                        cause_event_id=None),),
    events=(), laws=(),
)
limits = UnderworldLimits(world_id=W, max_hits_per_week=2, protected_person_ids=frozenset(),
                          protected_office_ids=frozenset({"mayor"}))


def hit(id, actor, target, **motive):
    return ChainStep(id=id, actor_org_id=actor, action="hit",
                     target=EntityRef(kind="person", id=target),
                     motive_relation_id=motive.get("relation"),
                     motive_event_id=None, motive_step_id=motive.get("answers"),
                     status="planned")


feud = Chain(id="feud", world_id=W, steps=(
    hit("s-1", "talleys", "sal", relation="grudge"),
    hit("s-2", "brenners", "rook", answers="s-1"),
    hit("s-3", "brenners", "ada", answers="s-2"),
    hit("s-4", "talleys", "iris", answers="s-2"),
    hit("s-5", "okafors", "rook", relation="grudge"),
))

# Play the feud out. A sent step is marked done before the next is judged,
# because a step only answers an earlier one that actually happened.
outcomes = []
sent = 0
for i, step in enumerate(feud.steps):
    verdict = validate_step(step, chain=feud, state=state, limits=limits,
                            hits_sent_this_week=sent)
    outcomes.append(verdict.outcome)
    print(f"{step.id}: {step.actor_org_id} -> {step.target.id}: {verdict.outcome} ({verdict.reason})")
    if verdict.outcome == "send":
        sent += 1
        steps = list(feud.steps)
        steps[i] = replace(step, status="done")
        feud = replace(feud, steps=tuple(steps))

assert outcomes == ["send", "send", "route_to_session", "drop", "defer"], outcomes
