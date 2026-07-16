"""Camp save / load persistence (includes settings)."""

from __future__ import annotations

import json
from pathlib import Path

from game.camp.meta import CampState
from game.models import Resources
from game.ui.settings import Settings

DEFAULT_SAVE_PATH = Path("save") / "camp.json"


def camp_to_dict(camp: CampState) -> dict:
    return {
        "resources": {
            "bone_dust": camp.resources.bone_dust,
            "hide": camp.resources.hide,
            "herb": camp.resources.herb,
            "metal": camp.resources.metal,
        },
        "built_buildings": sorted(camp.built_buildings),
        "boss_defeated": camp.boss_defeated,
    }


def camp_from_dict(data: dict) -> CampState:
    resources_data = data.get("resources", {})
    buildings = set(data.get("built_buildings", ["campfire"]))
    buildings.add("campfire")
    return CampState(
        resources=Resources(
            bone_dust=int(resources_data.get("bone_dust", 0)),
            hide=int(resources_data.get("hide", 0)),
            herb=int(resources_data.get("herb", 0)),
            metal=int(resources_data.get("metal", 0)),
        ),
        built_buildings=buildings,
        boss_defeated=bool(data.get("boss_defeated", False)),
    )


def save_game(camp: CampState, settings: Settings, path: Path | None = None) -> Path:
    save_path = path or DEFAULT_SAVE_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "camp": camp_to_dict(camp),
        "settings": settings.to_dict(),
    }
    save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return save_path


def load_game(path: Path | None = None) -> tuple[CampState, Settings]:
    save_path = path or DEFAULT_SAVE_PATH
    if not save_path.exists():
        return CampState(), Settings()
    try:
        data = json.loads(save_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return CampState(), Settings()
    if not isinstance(data, dict):
        return CampState(), Settings()

    # Backward compatible with older flat camp-only saves.
    if "camp" in data:
        camp = camp_from_dict(data.get("camp", {}))
        settings = Settings.from_dict(data.get("settings"))
    else:
        camp = camp_from_dict(data)
        settings = Settings()
    return camp, settings


# Keep old names for callers / tests.
def save_camp(camp: CampState, path: Path | None = None, settings: Settings | None = None) -> Path:
    return save_game(camp, settings or Settings(), path)


def load_camp(path: Path | None = None) -> CampState:
    camp, _ = load_game(path)
    return camp


def delete_save(path: Path | None = None) -> bool:
    save_path = path or DEFAULT_SAVE_PATH
    if save_path.exists():
        save_path.unlink()
        return True
    return False
