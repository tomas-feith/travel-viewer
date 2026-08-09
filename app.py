"""Countries visited - click the map, or the chips, to toggle a country."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from travel_viewer import stats, storage, worldmap
from travel_viewer.countries import BY_ALPHA2

DATA_PATH = Path(os.environ.get("TRAVEL_VIEWER_DATA", "visited.json"))

st.set_page_config(page_title="Countries visited", page_icon=":material/public:", layout="wide")


def _sync_region(key: str, shown: tuple[str, ...]) -> None:
    """Fold a chip group's selection back into the visited set.

    Only ``shown`` codes are reconciled, so a group filtered by search cannot
    clear countries that happen to be hidden at the time.
    """
    selected = set(st.session_state[key])
    visited: set[str] = st.session_state.visited
    visited.difference_update(shown)
    visited.update(selected)
    storage.save(visited, DATA_PATH)


if "visited" not in st.session_state:
    try:
        st.session_state.visited = storage.load(DATA_PATH)
    except storage.VisitedFileError as exc:
        st.error(f"Could not read your saved countries.\n\n{exc}")
        st.stop()
    st.session_state.last_map_selection = ()

visited: set[str] = st.session_state.visited
theme = getattr(getattr(st.context, "theme", None), "type", "light")

# --- Header ---------------------------------------------------------------

overall = stats.overall(visited)
header_left, header_right = st.columns([2, 3], vertical_alignment="center")
with header_left:
    st.metric("Countries visited", f"{overall.visited} / {overall.total}")
with header_right:
    st.progress(overall.fraction, text=f"{overall.percent}% of the world")

# --- Map ------------------------------------------------------------------

# The view is owned here rather than by the mouse: toggling a country rebuilds the
# figure, and Streamlit reseeds the chart from it, so mouse pan/zoom would be lost.
# Re-supplying the view on every rebuild makes it stick.
view = st.segmented_control(
    "Zoom to",
    options=list(worldmap.VIEWS),
    default=worldmap.DEFAULT_VIEW,
    key="map_view",
    label_visibility="collapsed",
)

event = st.plotly_chart(
    worldmap.build(visited, theme, view or worldmap.DEFAULT_VIEW),
    key="world_map",
    on_select="rerun",
    selection_mode="points",
    config={
        "displayModeBar": True,
        "displaylogo": False,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ["select2d", "lasso2d", "toImage"],
    },
)

# Plotly keeps the selection in widget state across reruns, so compare against the
# last one handled - otherwise an unrelated rerun would toggle the country again.
selection = tuple(sorted(event["selection"]["point_indices"]))
if selection != st.session_state.last_map_selection:
    st.session_state.last_map_selection = selection
    clicked = worldmap.clicked_codes(list(selection))
    if clicked:
        visited.symmetric_difference_update(clicked)
        storage.save(visited, DATA_PATH)
        st.rerun()

st.caption(
    "Click a country to toggle it, or drag a box to zoom in. Use the buttons above to "
    "jump to a region - mouse zoom resets when you toggle a country, region zoom does not."
)

# --- Search + region chips ------------------------------------------------

query = st.text_input(
    "Search countries",
    placeholder="Search for a country...",
    icon=":material/search:",
)
matches = {c.alpha2 for c in stats.search(query)} if query.strip() else None
if matches is not None and not matches:
    st.info(f"No country matches '{query.strip()}'.")

region_progress = stats.by_region(visited)
for region, progress in region_progress.items():
    countries = stats.in_region(region)
    if matches is not None:
        countries = [c for c in countries if c.alpha2 in matches]
        if not countries:
            continue

    label = f"{region} - {progress.visited}/{progress.total}"
    with st.expander(label, expanded=matches is not None, icon=":material/travel_explore:"):
        shown = tuple(c.alpha2 for c in countries)
        key = f"chips_{region}"
        # Drive the widget from the visited set so map clicks stay reflected here.
        st.session_state[key] = sorted(set(shown) & visited)
        st.pills(
            label,
            options=shown,
            format_func=lambda code: BY_ALPHA2[code].name,
            selection_mode="multi",
            key=key,
            on_change=_sync_region,
            args=(key, shown),
            label_visibility="collapsed",
            width="stretch",
        )

# --- Footer ---------------------------------------------------------------

with st.popover("Reset", icon=":material/restart_alt:"):
    st.markdown(f"Clear all **{overall.visited}** countries? This cannot be undone.")
    if st.button("Clear everything", type="primary"):
        visited.clear()
        storage.save(visited, DATA_PATH)
        st.rerun()
