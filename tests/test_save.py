"""Tests for camp save / load and settings."""

from pathlib import Path

from game.camp.meta import CampState
from game.camp.save import (
    camp_from_dict,
    camp_to_dict,
    delete_save,
    load_camp,
    load_game,
    save_camp,
    save_game,
)
from game.models import Resources
from game.ui.settings import TUTORIAL_STEPS, Settings


def test_camp_round_trip_dict() -> None:
    camp = CampState(
        resources=Resources(bone_dust=3, hide=4, herb=5, metal=6),
        built_buildings={"campfire", "gymnasium"},
        boss_defeated=True,
    )
    restored = camp_from_dict(camp_to_dict(camp))
    assert restored.resources.metal == 6
    assert "gymnasium" in restored.built_buildings
    assert restored.boss_defeated is True


def test_save_and_load_file(tmp_path: Path) -> None:
    path = tmp_path / "camp.json"
    camp = CampState(
        resources=Resources(bone_dust=10, hide=2),
        built_buildings={"campfire", "smithy"},
        boss_defeated=False,
    )
    save_camp(camp, path)
    loaded = load_camp(path)
    assert loaded.resources.bone_dust == 10
    assert "smithy" in loaded.built_buildings


def test_load_missing_file_returns_fresh_camp(tmp_path: Path) -> None:
    loaded = load_camp(tmp_path / "missing.json")
    assert loaded.resources.bone_dust == 0
    assert loaded.built_buildings == {"campfire"}


def test_delete_save(tmp_path: Path) -> None:
    path = tmp_path / "camp.json"
    save_camp(CampState(resources=Resources(metal=1)), path)
    assert delete_save(path) is True
    assert not path.exists()


def test_save_game_includes_settings(tmp_path: Path) -> None:
    path = tmp_path / "camp.json"
    camp = CampState(resources=Resources(herb=7))
    settings = Settings(sound_enabled=False, fullscreen=True, tutorial_done=True)
    save_game(camp, settings, path)
    loaded_camp, loaded_settings = load_game(path)
    assert loaded_camp.resources.herb == 7
    assert loaded_settings.sound_enabled is False
    assert loaded_settings.fullscreen is True
    assert loaded_settings.tutorial_done is True


def test_legacy_flat_save_loads_as_camp(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    path.write_text(
        '{"resources":{"bone_dust":2,"hide":0,"herb":0,"metal":0},'
        '"built_buildings":["campfire"],"boss_defeated":false}',
        encoding="utf-8",
    )
    camp, settings = load_game(path)
    assert camp.resources.bone_dust == 2
    assert settings.sound_enabled is True
    assert settings.tutorial_done is False


def test_tutorial_steps_are_complete() -> None:
    assert len(TUTORIAL_STEPS) >= 5
    assert all("title" in step and "body" in step for step in TUTORIAL_STEPS)
