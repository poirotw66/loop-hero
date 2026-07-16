"""Tests for tile combo resolution."""

from game.content.loader import ContentRegistry
from game.core.map import GameMap
from game.models import PlacedTile
from game.systems.combo_resolver import resolve_combos


def test_meadow_combo_becomes_blooming_meadow() -> None:
    content = ContentRegistry()
    game_map = GameMap()
    game_map.grid[(6, 5)] = PlacedTile(card_id="meadow")
    game_map.grid[(6, 6)] = PlacedTile(card_id="rock")
    triggered = resolve_combos(content, game_map)
    assert "COMBO-01" in triggered
    assert game_map.grid[(6, 5)].card_id == "blooming_meadow"


def test_village_combo_spawns_bandit_camp() -> None:
    content = ContentRegistry()
    game_map = GameMap()
    game_map.set_road_tile(2, PlacedTile(card_id="village"))
    game_map.set_road_tile(4, PlacedTile(card_id="village"))
    triggered = resolve_combos(content, game_map)
    assert "COMBO-04" in triggered
    assert game_map.count_card_in_grid("bandit_camp") == 1


def test_mountain_peak_from_3x3_rocks() -> None:
    content = ContentRegistry()
    game_map = GameMap()
    for row in range(4, 7):
        for col in range(4, 7):
            game_map.grid[(row, col)] = PlacedTile(card_id="rock")
    triggered = resolve_combos(content, game_map)
    assert "COMBO-02" in triggered
    assert any(tile.card_id == "mountain_peak" for tile in game_map.grid.values())
