"""The choropleth world map.

Plotly's ``locationmode="ISO-3"`` carries its own country geometry, so there is no
map file to ship or keep up to date. Trace order is fixed to ``COUNTRIES``, which
is what lets a click's ``point_index`` be mapped straight back to an alpha-2 code.
"""

from __future__ import annotations

from typing import NamedTuple

import plotly.graph_objects as go

from travel_viewer.countries import COUNTRIES

# Index -> alpha-2, matching the order points are added to the trace below.
TRACE_ORDER: tuple[str, ...] = tuple(c.alpha2 for c in COUNTRIES)


class Palette(NamedTuple):
    """Map colors for one theme."""

    visited: str
    unvisited: str
    border: str
    ocean: str


LIGHT = Palette(visited="#0f766e", unvisited="#e2e8f0", border="#ffffff", ocean="#f8fafc")
DARK = Palette(visited="#2dd4bf", unvisited="#1e293b", border="#0f172a", ocean="#0b1220")


def palette_for(theme: str) -> Palette:
    """Palette matching the app's active theme."""
    return DARK if theme == "dark" else LIGHT


def build(visited: set[str], theme: str = "light") -> go.Figure:
    """Build the world map with ``visited`` countries filled in."""
    colors = palette_for(theme)

    fig = go.Figure(
        go.Choropleth(
            locations=[c.alpha3 for c in COUNTRIES],
            locationmode="ISO-3",
            z=[1 if c.alpha2 in visited else 0 for c in COUNTRIES],
            zmin=0,
            zmax=1,
            text=[c.name for c in COUNTRIES],
            customdata=list(TRACE_ORDER),
            colorscale=[[0.0, colors.unvisited], [1.0, colors.visited]],
            showscale=False,
            marker_line_color=colors.border,
            marker_line_width=0.4,
            hovertemplate="<b>%{text}</b><extra></extra>",
            # Plotly dims unselected points once a selection exists; keep both
            # states fully opaque so one click does not grey out the whole map.
            selected={"marker": {"opacity": 1.0}},
            unselected={"marker": {"opacity": 1.0}},
        )
    )
    fig.update_geos(
        projection_type="natural earth",
        showframe=False,
        showcoastlines=False,
        showcountries=False,
        # Territories outside the 195 are not in the trace; painting the base land
        # the unvisited color keeps the map visually continuous.
        showland=True,
        landcolor=colors.unvisited,
        showocean=True,
        oceancolor=colors.ocean,
        lataxis_range=[-58, 85],
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        clickmode="event+select",
    )
    return fig


def clicked_codes(point_indices: list[int]) -> list[str]:
    """Map selected trace indices back to alpha-2 codes, ignoring stale indices."""
    return [TRACE_ORDER[i] for i in point_indices if 0 <= i < len(TRACE_ORDER)]
