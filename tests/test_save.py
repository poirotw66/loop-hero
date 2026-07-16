"""Tests for camp save / load."""

from pathlib import Path

from game.camp.meta import CampState
from game.camp.save import camp_from_dict, camp_to_dict, delete_save, load_camp, save_camp
from game.models import Resources


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
