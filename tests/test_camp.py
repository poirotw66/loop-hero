"""Tests for camp tile pass-through behavior."""

from game.camp.meta import CampState
from game.content.loader import ContentRegistry
from game.core.game_state import GameState
from game.systems.tile_effects import on_pass_road_tile


def test_camp_heals_even_without_card_def() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.hero_stats.hp = 50
    on_pass_road_tile(state, 0)
    assert state.hero_stats.hp == 85  # +35% of 100


def test_camp_spawns_boss_when_pending() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.boss_pending = True
    on_pass_road_tile(state, 0)
    assert not state.boss_pending
    assert "void_warden" in state.map.road_tile_at(0).spawned_enemies
