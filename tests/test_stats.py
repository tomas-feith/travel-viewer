"""Counting, filtering and search."""

from __future__ import annotations

from travel_viewer import stats
from travel_viewer.countries import COUNTRIES, REGIONS


def test_overall_of_empty() -> None:
    progress = stats.overall(set())
    assert progress == (0, 195)
    assert progress.fraction == 0.0
    assert progress.percent == 0


def test_overall_counts_only_known_codes() -> None:
    assert stats.overall({"PT", "ES", "ZZ"}).visited == 2


def test_overall_of_everything_is_100_percent() -> None:
    progress = stats.overall({c.alpha2 for c in COUNTRIES})
    assert progress == (195, 195)
    assert progress.percent == 100


def test_percent_rounds_for_display() -> None:
    # 47/195 is 24.1%
    assert stats.Progress(47, 195).percent == 24


def test_by_region_totals_match_the_world() -> None:
    per_region = stats.by_region({"PT", "JP", "BR", "ZA", "FJ"})
    assert list(per_region) == list(REGIONS)
    assert sum(p.total for p in per_region.values()) == 195
    assert sum(p.visited for p in per_region.values()) == 5


def test_by_region_attributes_countries_correctly() -> None:
    per_region = stats.by_region({"PT", "JP"})
    assert per_region["Europe"].visited == 1
    assert per_region["Asia"].visited == 1
    assert per_region["Africa"].visited == 0


def test_in_region_is_alphabetical_and_complete() -> None:
    africa = stats.in_region("Africa")
    assert len(africa) == 54
    assert [c.name for c in africa] == sorted(c.name for c in africa)


def test_in_region_unknown_region_is_empty() -> None:
    assert stats.in_region("Atlantis") == []


def test_search_is_case_insensitive_substring() -> None:
    assert "PT" in {c.alpha2 for c in stats.search("portug")}
    assert "PT" in {c.alpha2 for c in stats.search("PORTUGAL")}


def test_search_ranks_exact_code_matches_first() -> None:
    # "pt" is Portugal's code but also appears inside "Egypt".
    assert [c.alpha2 for c in stats.search("pt")] == ["PT", "EG"]
    assert [c.alpha2 for c in stats.search("prt")] == ["PT"]


def test_search_prefers_prefix_matches() -> None:
    # "Niger" is a substring of "Nigeria", but the exact prefix should come first.
    names = [c.name for c in stats.search("niger")]
    assert names[:2] == ["Niger", "Nigeria"]


def test_blank_search_returns_nothing() -> None:
    assert stats.search("") == []
    assert stats.search("   ") == []


def test_search_with_no_match() -> None:
    assert stats.search("atlantis") == []
