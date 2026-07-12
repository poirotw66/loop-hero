"""Tests for card placement rules."""

import pytest

from game.content.loader import ContentRegistry
from game.core.map import GameMap
from game.systems.placement import PlacementError, can_place_card, place_card


@pytest.fixture
def content() -> ContentRegistry:
    return ContentRegistry()


def test_road_card_replaces_wasteland(content: ContentRegistry) -> None:
    game_map = GameMap()
    assert can_place_card(content, game_map, "cemetery", loop_index=2)
    place_card(content, game_map, "cemetery", loop_index=2)
    assert game_map.road_tile_at(2).card_id == "cemetery"


def test_cannot_place_on_camp(content: ContentRegistry) -> None:
    game_map = GameMap()
    assert not can_place_card(content, game_map, "cemetery", loop_index=0)


def test_landscape_requires_distance_from_road(content: ContentRegistry) -> None:
    game_map = GameMap()
    assert can_place_card(content, game_map, "rock", grid_pos=(3, 3))
    assert not can_place_card(content, game_map, "rock", grid_pos=(1, 2))


def test_roadside_must_touch_road(content: ContentRegistry) -> None:
    game_map = GameMap()
    assert can_place_card(content, game_map, "spider_cocoon", grid_pos=(1, 1))
    assert not can_place_card(content, game_map, "spider_cocoon", grid_pos=(3, 3))


def test_placement_error_on_invalid(content: ContentRegistry) -> None:
    game_map = GameMap()
    with pytest.raises(PlacementError):
        place_card(content, game_map, "rock", grid_pos=(1, 2))
