"""A city of rival families: the world model, built by hand.

Harbour City has an elected mayor, three mob families with turf in different
districts, and a villain organisation with a nest in the docks. One family
holds a grudge against another, and the underworld plans a short feud. Each
planned step is validated against the world and the GM's limits.

Uses kirby-world (the geography) and kirby-campaign (everything else) only.
Every name is invented.
"""
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


def family(id, name, kind, head, turf):
    return Organisation(id=id, world_id=W, name=name, kind=kind, head_id=head, heir_id=None,
                        member_ids=(head,), territory=turf, influence=None, wealth=None,
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
limits = UnderworldLimits(world_id=W, max_hits_per_week=1, protected_person_ids=frozenset(),
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
))

sent = 0
for step in feud.steps:
    verdict = validate_step(step, state=state, limits=limits, hits_sent_this_week=sent)
    if verdict.outcome == "send":
        sent += 1
    print(f"{step.id}: {step.actor_org_id} -> {step.target.id}: {verdict.outcome} ({verdict.reason})")

assert [validate_step(s, state=state, limits=limits, hits_sent_this_week=0).outcome
        for s in feud.steps] == ["send", "send", "route_to_session", "drop"]
