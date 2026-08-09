"""The map figure and the click-index -> country mapping."""

from __future__ import annotations

import pytest

from travel_viewer import worldmap
from travel_viewer.countries import COUNTRIES


def test_trace_order_matches_country_table() -> None:
    assert tuple(c.alpha2 for c in COUNTRIES) == worldmap.TRACE_ORDER


def test_clicked_codes_maps_index_to_country() -> None:
    index = worldmap.TRACE_ORDER.index("PT")
    assert worldmap.clicked_codes([index]) == ["PT"]


def test_clicked_codes_ignores_out_of_range_indices() -> None:
    assert worldmap.clicked_codes([-1, 10_000]) == []


def test_clicked_codes_handles_empty_selection() -> None:
    assert worldmap.clicked_codes([]) == []


def test_figure_marks_visited_countries() -> None:
    fig = worldmap.build({"PT", "JP"})
    trace = fig.data[0]
    assert len(trace.z) == len(COUNTRIES)
    assert sum(trace.z) == 2
    assert trace.z[worldmap.TRACE_ORDER.index("PT")] == 1
    assert trace.z[worldmap.TRACE_ORDER.index("ES")] == 0


def test_figure_uses_iso3_locations() -> None:
    trace = worldmap.build(set()).data[0]
    assert trace.locationmode == "ISO-3"
    assert trace.locations[worldmap.TRACE_ORDER.index("US")] == "USA"


def test_figure_customdata_carries_alpha2() -> None:
    trace = worldmap.build(set()).data[0]
    assert tuple(trace.customdata) == worldmap.TRACE_ORDER


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_themes_produce_distinct_visited_colors(theme: str) -> None:
    palette = worldmap.palette_for(theme)
    assert palette.visited != palette.unvisited
    worldmap.build({"PT"}, theme)


def test_unknown_theme_falls_back_to_light() -> None:
    assert worldmap.palette_for("solarized") == worldmap.LIGHT
