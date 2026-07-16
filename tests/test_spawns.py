"""Tests for tile spawn targeting (enemies must appear on roads)."""

from game.camp.meta import CampState
from game.content.loader import ContentRegistry
from game.core.game_state import GameState
from game.models import PlacedTile
from game.systems.tile_effects import on_new_day


def test_mountain_peak_spawns_harpy_on_road() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.map.grid[(0, 0)] = PlacedTile(card_id="mountain_peak")
    state.day_count = 2
    on_new_day(state)
    assert state.map.grid[(0, 0)].spawned_enemies == []
    road_enemies = [e for tile in state.map.road_tiles for e in tile.spawned_enemies]
    assert "harpy" in road_enemies


def test_empty_treasury_spawns_gargoyle_on_road() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.map.grid[(6, 6)] = PlacedTile(card_id="empty_treasury")
    state.day_count = 3
    on_new_day(state)
    assert state.map.grid[(6, 6)].spawned_enemies == []
    road_enemies = [e for tile in state.map.road_tiles for e in tile.spawned_enemies]
    assert "gargoyle" in road_enemies


def test_bandit_camp_spawns_on_road() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.map.grid[(0, 1)] = PlacedTile(card_id="bandit_camp")
    state.day_count = 2
    on_new_day(state)
    assert state.map.grid[(0, 1)].spawned_enemies == []
    road_enemies = [e for tile in state.map.road_tiles for e in tile.spawned_enemies]
    assert "bandit" in road_enemies
