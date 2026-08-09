"""Round-tripping and resilience of the visited file."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travel_viewer import storage


def test_missing_file_is_empty_not_an_error(tmp_path: Path) -> None:
    assert storage.load(tmp_path / "nope.json") == set()


def test_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    storage.save({"PT", "ES", "JP"}, path)
    assert storage.load(path) == {"PT", "ES", "JP"}


def test_saved_file_is_sorted_and_versioned(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    storage.save({"JP", "ES", "PT"}, path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == storage.SCHEMA_VERSION
    assert list(raw["countries"]) == ["ES", "JP", "PT"]


def test_empty_set_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    storage.save(set(), path)
    assert storage.load(path) == set()


def test_unknown_codes_are_dropped(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    path.write_text(
        json.dumps({"version": 1, "countries": {"PT": {"visited": True}, "ZZ": {"visited": True}}}),
        encoding="utf-8",
    )
    assert storage.load(path) == {"PT"}


def test_visited_false_is_not_visited(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    path.write_text(
        json.dumps(
            {"version": 1, "countries": {"PT": {"visited": False}, "ES": {"visited": True}}}
        ),
        encoding="utf-8",
    )
    assert storage.load(path) == {"ES"}


def test_malformed_entries_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    path.write_text(
        json.dumps({"version": 1, "countries": {"PT": "yes", "ES": None, "JP": {"visited": True}}}),
        encoding="utf-8",
    )
    assert storage.load(path) == {"JP"}


def test_invalid_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(storage.VisitedFileError):
        storage.load(path)


def test_non_object_root_raises(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(storage.VisitedFileError):
        storage.load(path)


def test_save_leaves_no_temp_files_behind(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    storage.save({"PT"}, path)
    storage.save({"PT", "ES"}, path)
    assert [p.name for p in tmp_path.iterdir()] == ["visited.json"]


def test_save_creates_missing_parent_directory(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "visited.json"
    storage.save({"PT"}, path)
    assert storage.load(path) == {"PT"}


def test_save_overwrites_rather_than_merging(tmp_path: Path) -> None:
    path = tmp_path / "visited.json"
    storage.save({"PT", "ES"}, path)
    storage.save({"JP"}, path)
    assert storage.load(path) == {"JP"}
