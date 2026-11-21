"""Polities, the offices in them, and who held each office when."""
import pytest
from kirby_world import SourceRef

from kirby_campaign import Office, Polity, Tenure, WorldDate

D = WorldDate


def _polity(**over):
    fields = {"id": "harbour-city", "world_id": "w-1", "name": "Harbour City", "kind": "city_state",
                  "political_system": "Republic", "active": True, "capital_locale_id": "riverside",
                  "territory": ("riverside", "old-quarter"), "color": None, "source_ref": None,
                  "source_status": None}
    fields.update(over)
    return Polity(**fields)


def _tenure(**over):
    fields = {"id": "t-1", "world_id": "w-1", "office_id": "mayor", "person_id": "p-mayor",
                  "started": D(year=120, month=1, day=1), "ended": None, "how": "elected",
              "source_ref": None, "source_status": None}
    fields.update(over)
    return Tenure(**fields)


def test_a_polity_holds_territory_and_a_capital_inside_it():
    p = _polity()
    assert p.capital_locale_id in p.territory
    with pytest.raises(ValueError, match="capital"):
        _polity(capital_locale_id="bay")


def test_an_unknown_polity_kind_is_refused():
    with pytest.raises(ValueError, match="empire"):
        _polity(kind="empire")


def test_a_polity_from_a_source_says_whether_it_is_still_there():
    ref = SourceRef(source="fms", world_id="w-1", kind="nation", external_id="0")
    with pytest.raises(ValueError, match="source_status"):
        _polity(source_ref=ref, source_status=None)


def test_an_office_has_a_scope():
    mayor = Office(id="mayor", world_id="w-1", title="Mayor", polity_id="harbour-city",
                   scope_kind="polity", scope_id="harbour-city", source_ref=None, source_status=None)
    assert mayor.scope_kind == "polity"
    with pytest.raises(ValueError, match="county"):
        Office(id="x", world_id="w-1", title="X", polity_id="harbour-city",
               scope_kind="county", scope_id="y", source_ref=None, source_status=None)


def test_a_tenure_is_open_until_it_ends():
    assert _tenure().is_open
    assert not _tenure(ended=D(year=121, month=1, day=1)).is_open


def test_a_tenure_cannot_end_before_it_starts():
    with pytest.raises(ValueError, match="t-1"):
        _tenure(ended=D(year=119, month=1, day=1))


def test_how_a_tenure_began_is_a_closed_set():
    with pytest.raises(ValueError, match="bought"):
        _tenure(how="bought")
