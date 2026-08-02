"""Tests for oblivion removal and chapter progression."""

from game.camp.meta import CampState
from game.content.loader import ContentRegistry
from game.core.game_state import GameState
from game.core.map import GameMap
from game.models import PlacedTile
from game.systems.placement import can_place_card, place_card
from game.systems.tile_effects import on_pass_road_tile


def test_oblivion_removes_road_tile() -> None:
    content = ContentRegistry()
    game_map = GameMap()
    place_card(content, game_map, "cemetery", loop_index=2)
    assert can_place_card(content, game_map, "oblivion", loop_index=2)
    place_card(content, game_map, "oblivion", loop_index=2)
    assert game_map.road_tile_at(2).card_id == "wasteland"


def test_oblivion_removes_grid_tile() -> None:
    content = ContentRegistry()
    game_map = GameMap()
    place_card(content, game_map, "rock", grid_pos=(6, 6))
    assert can_place_card(content, game_map, "oblivion", grid_pos=(6, 6))
    place_card(content, game_map, "oblivion", grid_pos=(6, 6))
    assert (6, 6) not in game_map.grid


def test_oblivion_cannot_target_camp_or_empty() -> None:
    content = ContentRegistry()
    game_map = GameMap()
    assert not can_place_card(content, game_map, "oblivion", loop_index=0)
    assert not can_place_card(content, game_map, "oblivion", loop_index=2)
    assert not can_place_card(content, game_map, "oblivion", grid_pos=(6, 6))


def test_oblivion_reduces_boss_meter() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.hand = ["cemetery", "oblivion"]
    assert state.place_card_from_hand("cemetery", loop_index=2)
    assert state.boss_meter == 8
    assert state.place_card_from_hand("oblivion", loop_index=2)
    assert state.boss_meter == 0


def test_chapter_two_unlocks_after_boss() -> None:
    content = ContentRegistry()
    camp = CampState()
    assert camp.chapter_unlocked(content, "chapter_1")
    assert not camp.chapter_unlocked(content, "chapter_2")
    camp.boss_defeated = True
    assert camp.chapter_unlocked(content, "chapter_2")


def test_chapter_two_starter_and_boss() -> None:
    content = ContentRegistry()
    camp = CampState(boss_defeated=True)
    state = GameState(content=content, camp=camp)
    state.start_expedition("chapter_2")
    assert state.chapter_id == "chapter_2"
    assert state.boss_meter_max == 72
    assert "oblivion" in state.hand
    assert "thicket" in state.hand
    state.boss_pending = True
    on_pass_road_tile(state, 0)
    assert "memory_rift" in state.map.road_tile_at(0).spawned_enemies


def test_intel_archive_unlocks_oblivion_family() -> None:
    content = ContentRegistry()
    camp = CampState(built_buildings={"campfire", "intel_archive"})
    unlocked = camp.unlocked_cards(content)
    assert "oblivion" in unlocked
    assert "desert" in unlocked
    assert "beacon" in unlocked
    assert "chrono_crystal" in unlocked


def test_ruins_pass_gives_metal() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.map.set_road_tile(3, PlacedTile(card_id="ruins"))
    before = state.run_resources.metal
    on_pass_road_tile(state, 3)
    assert state.run_resources.metal == before + 1


def test_chapters_loaded() -> None:
    content = ContentRegistry()
    assert "chapter_1" in content.chapters
    assert content.chapters["chapter_2"].boss_id == "memory_rift"
