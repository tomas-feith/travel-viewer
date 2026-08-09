# travel-viewer

A one-page map of the countries you have visited. Click a country to toggle it;
the map, the counters and the per-region lists all stay in sync.

- **195 sovereign states** (193 UN members + Vatican City + Palestine)
- **Click the map** to toggle, or use the per-region chip lists for small countries
  that are hard to hit (Singapore, Malta, Liechtenstein...)
- **Search** by name or ISO code to filter the lists
- **Plain JSON storage** in `visited.json` - hand-editable, diffable, yours

## Running it

```powershell
uv sync
uv run streamlit run app.py
```

## Your data

Your travel history lives in `visited.json` at the repo root. It is **gitignored**,
so it never leaves your machine. See `visited.example.json` for the format:

```json
{
  "version": 1,
  "countries": { "PT": { "visited": true } }
}
```

Only visited countries are stored - absence means not visited. Each country maps to
an object rather than a bare `true` so fields like a year or a `lived in` / `transited`
status can be added later without changing the format.

Point the app at a different file with `TRAVEL_VIEWER_DATA`:

```powershell
$env:TRAVEL_VIEWER_DATA = "C:\path\to\other.json"; uv run streamlit run app.py
```

## Layout

| Path | What it is |
| --- | --- |
| `app.py` | The Streamlit page - layout and event handling only |
| `travel_viewer/countries.py` | Generated table of the 195 states (do not edit by hand) |
| `travel_viewer/storage.py` | Atomic load/save of `visited.json` |
| `travel_viewer/stats.py` | Pure counting, filtering and search |
| `travel_viewer/worldmap.py` | The Plotly choropleth and click-index mapping |
| `scripts/gen_countries.py` | Dev-only regenerator for the country table |

The map uses Plotly's built-in `locationmode="ISO-3"` geometry, so there is no map
data file to ship or keep current.

## Development

```powershell
uv run ruff check .
uv run ruff format .
uv run mypy
uv run pytest
```

Install the hooks so the same checks run before each commit:

```powershell
uv run pre-commit install
```

To regenerate the country table (only needed if the sovereign-state list changes):

```powershell
uv run --with pycountry --with pycountry-convert python scripts/gen_countries.py
```

## Known rough edge

Plotly keeps a clicked country selected. Clicking the *same* country again first
clears that selection, so un-toggling from the map takes two clicks. The chip lists
toggle cleanly in one click either way.
