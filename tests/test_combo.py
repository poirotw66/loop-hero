"""Tests for tile combo resolution."""

from game.content.loader import ContentRegistry
from game.core.map import GameMap
from game.models import PlacedTile
from game.systems.combo_resolver import resolve_combos


def test_meadow_combo_becomes_blooming_meadow() -> None:
    content = ContentRegistry()
    game_map = GameMap()
    game_map.grid[(3, 3)] = PlacedTile(card_id="meadow")
    game_map.grid[(3, 4)] = PlacedTile(card_id="rock")
    triggered = resolve_combos(content, game_map)
    assert "COMBO-01" in triggered
    assert game_map.grid[(3, 3)].card_id == "blooming_meadow"


def test_village_combo_spawns_bandit_camp() -> None:
    content = ContentRegistry()
    game_map = GameMap()
    game_map.set_road_tile(2, PlacedTile(card_id="village"))
    game_map.set_road_tile(4, PlacedTile(card_id="village"))
    triggered = resolve_combos(content, game_map)
    assert "COMBO-04" in triggered
    assert game_map.count_card_in_grid("bandit_camp") == 1
