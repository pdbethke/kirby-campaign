"""A world shaped the way an importer from a world simulator will make it:
ids are the source's own ids as text, every record carries a SourceRef, the
source has pruned someone, and one organisation spans two of the source's
families. It must construct from kirby-world and kirby-campaign alone
(``test_independence.py`` forbids kirby_fms in this package; kirby-world's
leaf test forbids it there)."""
from kirby_world import SourceRef

from kirby_campaign import Kin, Office, Organisation, Polity, Rank, Tenure, WorldDate, WorldState
from tests.conftest import person

W = "w-fms"


def ref(kind, external_id):
    return SourceRef(source="fms", world_id=W, kind=kind, external_id=external_id)


def test_an_fms_shaped_world_constructs():
    people = (
        person("fms-person-2855", "Vidal Delorme", world_id=W, polity_id="fms-nation-0",
               source_ref=ref("person", "2855"), source_status="present",
               kin=Kin(spouse_ids=(), parent_ids=("fms-person-1",), child_ids=())),
        person("fms-person-1", "Viggo Delorme", world_id=W, polity_id="fms-nation-0",
               born=WorldDate(year=-40, month=6, day=1), died=WorldDate(year=4, month=2, day=1),
               source_ref=ref("person", "1"),
               source_status="gone"),
    )
    state = WorldState(
        world_id=W,
        polities=(Polity(id="fms-nation-0", world_id=W, name="Sundgauvian", kind="nation",
                         political_system="Federation", active=True, capital_locale_id=None,
                         territory=("fms-province-0",), color=0xDABABF,
                         source_ref=ref("nation", "0"), source_status="present"),),
        offices=(Office(id="fms-nation-0-leader", world_id=W, title="Leader",
                        polity_id="fms-nation-0", scope_kind="polity",
                        scope_id="fms-nation-0"),),
        tenures=(Tenure(id="fms-reign-0-8", world_id=W, office_id="fms-nation-0-leader",
                        person_id="fms-person-2855", started=WorldDate(year=129, month=2, day=1),
                        ended=None, how="elected"),),
        people=people,
        organisations=(Organisation(
            id="fms-org-delorme", world_id=W, name="Delorme", kind="dynasty",
            ranks=(Rank(name="patriarch", archetype_character_id=None, hit_failure_base=0.5,
                        guards=2),
                   Rank(name="member", archetype_character_id=None, hit_failure_base=0.1,
                        guards=0)),
            head_id="fms-person-2855", heir_id=None,
            territory=("fms-province-0",), influence=40.0, wealth=12.0,
            source_refs=(ref("family", "1"), ref("family", "31")), source_status="present"),),
        relations=(), events=(), laws=(),
    )
    assert tuple(p.id for p in state.holders_of("fms-nation-0-leader")) == ("fms-person-2855",)
    assert state.person("fms-person-1").source_status == "gone"
    assert not state.has_person("fms-person-404")

