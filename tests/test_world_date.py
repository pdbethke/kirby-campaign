"""A date in a campaign world's calendar."""
import pytest

from kirby_campaign import WorldDate


def test_dates_order_like_dates():
    assert WorldDate(year=1, month=12, day=31) < WorldDate(year=2, month=1, day=1)
    assert str(WorldDate(year=121, month=10, day=18)) == "0121-10-18"


def test_backstory_years_are_allowed():
    """A world's backstory (births of the people alive when it was made) can
    predate year 1."""
    assert str(WorldDate(year=-42, month=3, day=1)) == "-0042-03-01"
    assert WorldDate(year=0, month=6, day=1) < WorldDate(year=1, month=1, day=1)


@pytest.mark.parametrize("field, value", [("month", 13), ("month", 0), ("day", 0), ("day", 32)])
def test_month_and_day_are_checked(field, value):
    parts = {"year": 1, "month": 1, "day": 1, field: value}
    with pytest.raises(ValueError, match=field):
        WorldDate(**parts)
