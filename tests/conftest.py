"""One small world, shared by the world-state, campaign-layer and underworld tests.

Harbour City: an elected mayor, two feuding mob families, a villain
organisation, and one player character. Every name is invented.
"""
import pytest

from kirby_campaign import (
    Cause,
    EntityRef,
    Kin,
    Membership,
    Office,
    Organisation,
    Person,
    Polity,
    Rank,
    Relation,
    Tenure,
    WorldDate,
    WorldEvent,
)

W = "w-1"
NO_KIN = Kin(spouse_ids=(), parent_ids=(), child_ids=())


def person(id, english, **over):
    fields = {"id": id, "world_id": W, "names": {"English": english}, "gender": None,
              "born": WorldDate(year=80, month=1, day=1), "died": None,
              "polity_id": "harbour-city", "culture": None, "religion": None, "traits": (),
              "skills": {}, "kin": NO_KIN, "character_id": None, "pc": False,
              "campaign_id": None, "source_ref": None, "source_status": None}
    fields.update(over)
    return Person(**fields)


#: A mob family's ladder, highest first. Bosses are hard to hit and keep two guards.
MOB_RANKS = (
    Rank(name="boss", archetype_character_id="c-mob-boss", hit_failure_base=0.4, guards=2),
    Rank(name="lieutenant", archetype_character_id="c-gunman", hit_failure_base=0.2, guards=1),
    Rank(name="soldier", archetype_character_id="c-gunman", hit_failure_base=0.1, guards=0),
)


def organisation(id, name, kind, head, territory, *, ranks=MOB_RANKS, influence=50.0):
    return Organisation(id=id, world_id=W, name=name, kind=kind, ranks=ranks, head_id=head,
                        heir_id=None, territory=territory, influence=influence, wealth=None,
                        source_refs=(), source_status=None)


COIL_RANKS = (
    Rank(name="master", archetype_character_id="c-coilmaster", hit_failure_base=0.6, guards=2),
    Rank(name="agent", archetype_character_id="c-coil-agent", hit_failure_base=0.1, guards=0),
)


def membership(org, who, rank):
    return Membership(id=f"m-{org}-{who}", world_id=W, organisation_id=org, person_id=who,
                      rank=rank, started=None, ended=None, source_ref=None, source_status=None)


def world_records():
    """The records as a dict of WorldState's keyword arguments, so a test can
    swap one collection and build its own state."""
    return {
        "world_id": W,
        "polities": (Polity(id="harbour-city", world_id=W, name="Harbour City",
                            kind="city_state", political_system="Republic", active=True,
                            capital_locale_id="riverside",
                            territory=("riverside", "old-quarter", "the-docks"), color=None,
                            source_ref=None, source_status=None),),
        "offices": (Office(id="mayor", world_id=W, title="Mayor", polity_id="harbour-city",
                           scope_kind="polity", scope_id="harbour-city"),),
        "tenures": (Tenure(id="t-mayor", world_id=W, office_id="mayor", person_id="p-mayor",
                           started=WorldDate(year=120, month=1, day=1), ended=None,
                           how="elected"),),
        "people": (
            person("p-mayor", "Iris Calloway"),
            person("p-sal", "Sal Brenner"),
            person("p-rook", "Rook Talley"),
            person("p-coil", "The Coilmaster"),
            person("p-ada", "Ada Varga", pc=True, campaign_id="c-1"),
            person("p-dead", "Old Man Brenner", died=WorldDate(year=119, month=2, day=2)),
            person("p-vic", "Vic Brenner"), person("p-b1", "Joey Brenner"),
            person("p-b2", "Nico Marchetti"),
            person("p-tlt", "Mags Talley"), person("p-t1", "Lenny Shaw"),
            person("p-t2", "Dutch Okon"),
            person("p-ca", "Agent Ferro"), person("p-cb", "Agent Lusk"),
        ),
        "memberships": (
            membership("brenner-family", "p-sal", "boss"),
            membership("brenner-family", "p-vic", "lieutenant"),
            membership("brenner-family", "p-b1", "soldier"),
            membership("brenner-family", "p-b2", "soldier"),
            membership("talley-outfit", "p-rook", "boss"),
            membership("talley-outfit", "p-tlt", "lieutenant"),
            membership("talley-outfit", "p-t1", "soldier"),
            membership("talley-outfit", "p-t2", "soldier"),
            membership("the-coil", "p-coil", "master"),
            membership("the-coil", "p-ca", "agent"),
            membership("the-coil", "p-cb", "agent"),
        ),
        "organisations": (
            organisation("brenner-family", "The Brenner Family", "mob_family", "p-sal",
                         ("old-quarter",)),
            organisation("talley-outfit", "The Talley Outfit", "mob_family", "p-rook",
                         ("the-docks",)),
            organisation("the-coil", "The Coil", "villain_org", "p-coil", ("the-docks",),
                         ranks=COIL_RANKS),
        ),
        "relations": (Relation(id="r-grudge", world_id=W, kind="grudge",
                               a=EntityRef(kind="organisation", id="talley-outfit"),
                               b=EntityRef(kind="organisation", id="brenner-family"),
                               since=WorldDate(year=118, month=4, day=1), until=None,
                               cause_event_id=None),),
        "events": (WorldEvent(id="e-pier", world_id=W, date=WorldDate(year=121, month=10, day=9),
                              kind="hit", actors=("p-rook", "p-dead"), places=("the-docks",),
                              groups=(EntityRef(kind="organisation", id="talley-outfit"),),
                              truth="Rook Talley killed Old Man Brenner on the pier.",
                              public_account="A body was pulled from the river by the pier.",
                              cause=Cause(kind="chain", ref="ch-1"), source_ref=None),),
        "laws": (),
    }


@pytest.fixture
def records():
    return world_records()
