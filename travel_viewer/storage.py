"""Reading and writing the visited-countries file.

The on-disk format is deliberately boring so it stays hand-editable and diffable::

    {
      "version": 1,
      "countries": {"PT": {"visited": true}, "ES": {"visited": true}}
    }

Only visited countries are stored; absence means "not visited". The nested object
per country is there so extra fields (year, status) can be added later without a
format change.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from travel_viewer.countries import BY_ALPHA2

SCHEMA_VERSION = 1
DEFAULT_PATH = Path("visited.json")


class VisitedFileError(Exception):
    """Raised when the visited file exists but cannot be understood."""


def load(path: Path = DEFAULT_PATH) -> set[str]:
    """Return the set of visited alpha-2 codes, or an empty set if no file yet.

    Unknown codes are dropped rather than raising: the sovereign-state list can
    change between versions, and a stale code should not make the app unopenable.
    """
    if not path.exists():
        return set()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VisitedFileError(f"{path} is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise VisitedFileError(f"{path} should contain a JSON object, got {type(raw).__name__}")

    countries = raw.get("countries", {})
    if not isinstance(countries, dict):
        raise VisitedFileError(f"{path}: 'countries' should be an object")

    return {
        code
        for code, entry in countries.items()
        if code in BY_ALPHA2 and isinstance(entry, dict) and entry.get("visited") is True
    }


def save(visited: set[str], path: Path = DEFAULT_PATH) -> None:
    """Write ``visited`` to ``path`` atomically, sorted for a stable diff."""
    payload = {
        "version": SCHEMA_VERSION,
        "countries": {code: {"visited": True} for code in sorted(visited)},
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a sibling temp file first so an interrupted save cannot truncate
    # an existing good file.
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
