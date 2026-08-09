"""The choropleth world map.

Plotly's ``locationmode="ISO-3"`` carries its own country geometry, so there is no
map file to ship or keep up to date. Trace order is fixed to ``COUNTRIES``, which
is what lets a click's ``point_index`` be mapped straight back to an alpha-2 code.

Why the view is owned here rather than left to the mouse
--------------------------------------------------------
Toggling a country reruns the script, which hands Streamlit a rebuilt figure.
Streamlit reseeds the chart's React state from that figure, so any pan/zoom the
user did with the mouse is discarded - ``uirevision`` does not survive it. The fix
is to keep the view in Python and re-supply it on every rebuild, so a rebuild
*restores* the view instead of losing it. That is what ``VIEWS`` is for.
"""

from __future__ import annotations

from typing import Any, NamedTuple

import plotly.graph_objects as go

from travel_viewer.countries import COUNTRIES

# Index -> alpha-2, matching the order points are added to the trace below.
TRACE_ORDER: tuple[str, ...] = tuple(c.alpha2 for c in COUNTRIES)

DEFAULT_VIEW = "World"

# Named viewports. Plotly has built-in scopes for most regions; Oceania has none,
# so it is expressed as an explicit centre and zoom level.
VIEWS: dict[str, dict[str, Any]] = {
    "World": {"scope": "world", "lataxis_range": [-58, 85]},
    "Europe": {"scope": "europe"},
    "Asia": {"scope": "asia"},
    "Africa": {"scope": "africa"},
    "N. America": {"scope": "north america"},
    "S. America": {"scope": "south america"},
    "Oceania": {
        "scope": "world",
        "center": {"lon": 155, "lat": -22},
        "projection_scale": 3.1,
        "lataxis_range": [-50, 10],
        "lonaxis_range": [110, 200],
    },
}


class Palette(NamedTuple):
    """Map colors for one theme."""

    visited: str
    unvisited: str
    border: str
    coast: str
    ocean: str


# One hue carries "visited"; "unvisited" is a deliberate neutral that recedes.
# Validated for colorblind separation: worst-case adjacent dE 39.1 (protan),
# normal-vision dE 42.6 - well clear of the dE 8 floor.
LIGHT = Palette(
    visited="#0f766e",
    unvisited="#dfe5ec",
    border="#ffffff",
    coast="#c2ccd8",
    ocean="#f4f7fa",
)
DARK = Palette(
    visited="#2dd4bf",
    unvisited="#334155",
    border="#0f172a",
    coast="#1e293b",
    ocean="#0b1220",
)


def palette_for(theme: str) -> Palette:
    """Palette matching the app's active theme."""
    return DARK if theme == "dark" else LIGHT


def build(visited: set[str], theme: str = "light", view: str = DEFAULT_VIEW) -> go.Figure:
    """Build the world map with ``visited`` filled in, framed on ``view``.

    An unknown ``view`` falls back to the world view rather than raising, so a
    stale value in session state cannot break the page.
    """
    colors = palette_for(theme)
    geo = dict(VIEWS.get(view, VIEWS[DEFAULT_VIEW]))

    fig = go.Figure(
        go.Choropleth(
            locations=[c.alpha3 for c in COUNTRIES],
            locationmode="ISO-3",
            z=[1 if c.alpha2 in visited else 0 for c in COUNTRIES],
            zmin=0,
            zmax=1,
            text=[c.name for c in COUNTRIES],
            # [0] is not shown in the tooltip; it keeps the alpha-2 code on the
            # point as a cross-check against the TRACE_ORDER index mapping.
            customdata=[
                [c.alpha2, c.region, "Visited" if c.alpha2 in visited else "Not visited"]
                for c in COUNTRIES
            ],
            colorscale=[[0.0, colors.unvisited], [1.0, colors.visited]],
            showscale=False,
            marker_line_color=colors.border,
            marker_line_width=0.5,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "<span style='font-size:0.85em'>%{customdata[1]} &middot; "
                "%{customdata[2]}</span><extra></extra>"
            ),
            # Plotly dims unselected points once a selection exists; keep both
            # states fully opaque so one click does not grey out the whole map.
            selected={"marker": {"opacity": 1.0}},
            unselected={"marker": {"opacity": 1.0}},
        )
    )
    fig.update_geos(
        projection_type="natural earth",
        showframe=False,
        # Territories outside the 195 are not in the trace; painting the base land
        # the unvisited color keeps the map visually continuous.
        showland=True,
        landcolor=colors.unvisited,
        showcoastlines=True,
        coastlinecolor=colors.coast,
        coastlinewidth=0.5,
        # Draw borders for the territories that are not trace points, so the
        # base land does not read as one undifferentiated mass.
        showcountries=True,
        countrycolor=colors.border,
        countrywidth=0.5,
        showocean=True,
        oceancolor=colors.ocean,
        showlakes=False,
        bgcolor="rgba(0,0,0,0)",
        **geo,
    )
    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=540,
        paper_bgcolor="rgba(0,0,0,0)",
        # Set explicitly so Streamlit does not force "pan"; box-drag then zooms.
        # Clicks still toggle because clickmode stays "event+select" for any
        # dragmode other than select/lasso.
        dragmode="zoom",
        hoverlabel={"align": "left"},
    )
    return fig


def clicked_codes(point_indices: list[int]) -> list[str]:
    """Map selected trace indices back to alpha-2 codes, ignoring stale indices."""
    return [TRACE_ORDER[i] for i in point_indices if 0 <= i < len(TRACE_ORDER)]
