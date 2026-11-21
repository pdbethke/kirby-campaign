"""People: a world identity, which may link to a HERO build."""
import pytest
from kirby_world import SourceRef

from kirby_campaign import Kin, Person, WorldDate

D = WorldDate
NO_KIN = Kin(spouse_ids=(), parent_ids=(), child_ids=())


def _person(**over):
    fields = {"id": "p-ada", "world_id": "w-1", "names": {"English": "Ada Varga"},
              "gender": "Female", "born": D(year=90, month=5, day=2), "died": None,
              "polity_id": "harbour-city", "culture": None, "religion": None, "traits": (),
              "skills": {}, "kin": NO_KIN, "character_id": None, "pc": False,
              "campaign_id": None, "source_ref": None, "source_status": None}
    fields.update(over)
    return Person(**fields)


def test_a_name_is_asked_for_in_a_language():
    ada = _person()
    assert ada.name("English") == "Ada Varga"
    with pytest.raises(KeyError, match="English"):
        ada.name("German")


def test_a_person_needs_at_least_one_name():
    with pytest.raises(ValueError, match="names"):
        _person(names={})


def test_death_before_birth_is_refused():
    with pytest.raises(ValueError, match="p-ada"):
        _person(died=D(year=80, month=1, day=1))


def test_the_living_have_no_death_date():
    assert _person().alive
    assert not _person(died=D(year=120, month=1, day=1)).alive


def test_a_player_character_belongs_to_a_campaign_and_to_no_source():
    assert _person(pc=True, campaign_id="c-1").campaign_id == "c-1"
    with pytest.raises(ValueError, match="campaign_id"):
        _person(pc=True, campaign_id=None)
    ref = SourceRef(source="fms", world_id="w-1", kind="person", external_id="9")
    with pytest.raises(ValueError, match="source"):
        _person(pc=True, campaign_id="c-1", source_ref=ref, source_status="present")


def test_a_non_player_character_belongs_to_no_campaign():
    with pytest.raises(ValueError, match="campaign_id"):
        _person(pc=False, campaign_id="c-1")


def test_kin_may_name_people_the_world_no_longer_has():
    kin = Kin(spouse_ids=(), parent_ids=("p-404",), child_ids=())
    assert _person(kin=kin).kin.parent_ids == ("p-404",)


def test_nobody_is_their_own_kin():
    with pytest.raises(ValueError, match="p-ada"):
        _person(kin=Kin(spouse_ids=("p-ada",), parent_ids=(), child_ids=()))


def test_names_and_skills_are_read_only():
    ada = _person(skills={"administration": 72.0})
    with pytest.raises(TypeError):
        ada.names["German"] = "x"
    with pytest.raises(TypeError):
        ada.skills["charisma"] = 1.0
