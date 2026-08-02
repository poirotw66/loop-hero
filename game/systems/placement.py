"""Card placement validation."""

from __future__ import annotations

from game.content.loader import ContentRegistry
from game.core.map import GameMap, is_valid_landscape, is_valid_roadside, road_coord_for_index
from game.models import CardType, PlacedTile


class PlacementError(Exception):
    pass


def _is_oblivion(content: ContentRegistry, card_id: str) -> bool:
    card = content.cards.get(card_id)
    return bool(card and card.effects.get("remove_tile"))


def can_place_card(
    content: ContentRegistry,
    game_map: GameMap,
    card_id: str,
    *,
    loop_index: int | None = None,
    grid_pos: tuple[int, int] | None = None,
) -> bool:
    card = content.cards.get(card_id)
    if card is None:
        return False

    if _is_oblivion(content, card_id):
        if loop_index is not None:
            if loop_index == 0:
                return False
            return game_map.road_tile_at(loop_index).card_id not in {"camp", "wasteland"}
        if grid_pos is None:
            return False
        return grid_pos in game_map.grid

    if card.card_type == CardType.ROAD:
        if loop_index is None or loop_index == 0:
            return False
        road_tile = game_map.road_tile_at(loop_index)
        return road_tile.card_id in {"wasteland", "cemetery", "grove", "swamp", "village", "ruins"}

    if grid_pos is None:
        return False
    row, col = grid_pos
    if (row, col) in game_map.grid:
        return False

    if card.card_type == CardType.ROADSIDE:
        return is_valid_roadside(row, col)
    return is_valid_landscape(row, col)


def place_card(
    content: ContentRegistry,
    game_map: GameMap,
    card_id: str,
    *,
    loop_index: int | None = None,
    grid_pos: tuple[int, int] | None = None,
) -> tuple[int, int] | None:
    if not can_place_card(content, game_map, card_id, loop_index=loop_index, grid_pos=grid_pos):
        raise PlacementError(f"Cannot place card {card_id}")

    if _is_oblivion(content, card_id):
        if loop_index is not None:
            game_map.set_road_tile(loop_index, PlacedTile(card_id="wasteland"))
            return road_coord_for_index(loop_index)
        assert grid_pos is not None
        del game_map.grid[grid_pos]
        return grid_pos

    tile = PlacedTile(card_id=card_id)
    if loop_index is not None:
        game_map.set_road_tile(loop_index, tile)
        return road_coord_for_index(loop_index)

    assert grid_pos is not None
    game_map.grid[grid_pos] = tile
    return grid_pos
