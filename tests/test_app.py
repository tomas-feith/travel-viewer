"""End-to-end smoke tests: run app.py headlessly via Streamlit's AppTest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppTest:
    """An app instance pointed at a throwaway data file."""
    monkeypatch.setenv("TRAVEL_VIEWER_DATA", str(tmp_path / "visited.json"))
    return AppTest.from_file(APP, default_timeout=30)


def test_app_runs_clean_with_no_data(app: AppTest) -> None:
    app.run()
    assert not app.exception
    assert "0 / 195" in app.metric[0].value


def test_app_loads_existing_data(tmp_path: Path, app: AppTest) -> None:
    (tmp_path / "visited.json").write_text(
        json.dumps({"version": 1, "countries": {"PT": {"visited": True}, "JP": {"visited": True}}}),
        encoding="utf-8",
    )
    app.run()
    assert not app.exception
    assert "2 / 195" in app.metric[0].value


def test_app_renders_a_chip_group_per_region(app: AppTest) -> None:
    app.run()
    assert not app.exception
    assert len(app.pills) == 5
    assert {len(pills.options) for pills in app.pills} == {44, 48, 54, 35, 14}


def test_selecting_a_chip_persists_to_disk(tmp_path: Path, app: AppTest) -> None:
    app.run()
    europe = next(p for p in app.pills if len(p.options) == 44)
    europe.set_value(["PT", "ES"]).run()

    assert not app.exception
    assert "2 / 195" in app.metric[0].value
    saved = json.loads((tmp_path / "visited.json").read_text(encoding="utf-8"))
    assert sorted(saved["countries"]) == ["ES", "PT"]


def test_deselecting_a_chip_removes_it(tmp_path: Path, app: AppTest) -> None:
    (tmp_path / "visited.json").write_text(
        json.dumps({"version": 1, "countries": {"PT": {"visited": True}, "ES": {"visited": True}}}),
        encoding="utf-8",
    )
    app.run()
    europe = next(p for p in app.pills if len(p.options) == 44)
    europe.set_value(["PT"]).run()

    assert not app.exception
    saved = json.loads((tmp_path / "visited.json").read_text(encoding="utf-8"))
    assert sorted(saved["countries"]) == ["PT"]


def test_chip_group_does_not_clear_other_regions(tmp_path: Path, app: AppTest) -> None:
    (tmp_path / "visited.json").write_text(
        json.dumps({"version": 1, "countries": {"JP": {"visited": True}}}),
        encoding="utf-8",
    )
    app.run()
    europe = next(p for p in app.pills if len(p.options) == 44)
    europe.set_value(["PT"]).run()

    assert not app.exception
    saved = json.loads((tmp_path / "visited.json").read_text(encoding="utf-8"))
    assert sorted(saved["countries"]) == ["JP", "PT"]


def test_search_filters_to_matching_countries(app: AppTest) -> None:
    app.run()
    app.text_input[0].set_value("portugal").run()

    assert not app.exception
    assert len(app.pills) == 1
    # .options exposes the formatted labels, which confirms format_func is applied.
    assert app.pills[0].options == ["Portugal"]


def test_search_with_no_match_shows_a_message(app: AppTest) -> None:
    app.run()
    app.text_input[0].set_value("atlantis").run()

    assert not app.exception
    assert len(app.pills) == 0
    assert "No country matches" in app.info[0].value


def test_search_does_not_clear_countries_outside_the_filter(tmp_path: Path, app: AppTest) -> None:
    """A filtered chip group must only reconcile the countries it is showing."""
    (tmp_path / "visited.json").write_text(
        json.dumps({"version": 1, "countries": {"ES": {"visited": True}, "JP": {"visited": True}}}),
        encoding="utf-8",
    )
    app.run()
    app.text_input[0].set_value("portugal").run()
    app.pills[0].set_value(["PT"]).run()

    assert not app.exception
    saved = json.loads((tmp_path / "visited.json").read_text(encoding="utf-8"))
    assert sorted(saved["countries"]) == ["ES", "JP", "PT"]


def test_reset_clears_everything(tmp_path: Path, app: AppTest) -> None:
    (tmp_path / "visited.json").write_text(
        json.dumps({"version": 1, "countries": {"PT": {"visited": True}}}),
        encoding="utf-8",
    )
    app.run()
    app.button[0].click().run()

    assert not app.exception
    assert "0 / 195" in app.metric[0].value
    saved = json.loads((tmp_path / "visited.json").read_text(encoding="utf-8"))
    assert saved["countries"] == {}


def test_corrupt_data_file_shows_an_error_instead_of_crashing(tmp_path: Path, app: AppTest) -> None:
    (tmp_path / "visited.json").write_text("{not json", encoding="utf-8")
    app.run()

    assert not app.exception
    assert "Could not read your saved countries" in app.error[0].value
