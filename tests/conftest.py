"""One small world, shared by the world-state, campaign-layer and underworld tests.

Harbour City: an elected mayor, two feuding mob families, a villain
organisation, and one player character. Every name is invented.
"""
import pytest

from kirby_campaign import (
    Cause,
    EntityRef,
    Kin,
    Office,
    Organisation,
    Person,
    Polity,
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


def organisation(id, name, kind, head, members, territory):
    return Organisation(id=id, world_id=W, name=name, kind=kind, head_id=head, heir_id=None,
                        member_ids=members, territory=territory, influence=None, wealth=None,
                        source_refs=(), source_status=None)


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
        ),
        "organisations": (
            organisation("brenner-family", "The Brenner Family", "mob_family", "p-sal",
                         ("p-sal", "p-404"), ("old-quarter",)),
            organisation("talley-outfit", "The Talley Outfit", "mob_family", "p-rook",
                         ("p-rook",), ("the-docks",)),
            organisation("the-coil", "The Coil", "villain_org", "p-coil", ("p-coil",),
                         ("the-docks",)),
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
