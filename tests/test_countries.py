"""Guards on the generated country table."""

from __future__ import annotations

from travel_viewer.countries import BY_ALPHA2, COUNTRIES, REGIONS


def test_has_195_sovereign_states() -> None:
    assert len(COUNTRIES) == 195


def test_codes_are_unique_and_well_formed() -> None:
    assert len({c.alpha2 for c in COUNTRIES}) == 195
    assert len({c.alpha3 for c in COUNTRIES}) == 195
    assert all(len(c.alpha2) == 2 and c.alpha2.isupper() for c in COUNTRIES)
    assert all(len(c.alpha3) == 3 and c.alpha3.isupper() for c in COUNTRIES)


def test_every_country_lands_in_a_known_region() -> None:
    assert {c.region for c in COUNTRIES} == set(REGIONS)


def test_regions_partition_the_world() -> None:
    per_region = {r: sum(1 for c in COUNTRIES if c.region == r) for r in REGIONS}
    assert sum(per_region.values()) == 195
    # Sanity-check the two regions whose size is easiest to get wrong.
    assert per_region["Africa"] == 54
    assert per_region["Oceania"] == 14


def test_lookup_is_consistent() -> None:
    assert len(BY_ALPHA2) == 195
    assert BY_ALPHA2["PT"].name == "Portugal"
    assert BY_ALPHA2["US"].alpha3 == "USA"
