"""Card placement validation."""

from __future__ import annotations

from game.content.loader import ContentRegistry
from game.core.map import GameMap, is_valid_landscape, is_valid_roadside, road_coord_for_index
from game.models import CardType


class PlacementError(Exception):
    pass


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

    if card.card_type == CardType.ROAD:
        if loop_index is None or loop_index == 0:
            return False
        road_tile = game_map.road_tile_at(loop_index)
        return road_tile.card_id in {"wasteland", "cemetery", "grove", "swamp", "village"}

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

    from game.models import PlacedTile

    tile = PlacedTile(card_id=card_id)
    if loop_index is not None:
        game_map.set_road_tile(loop_index, tile)
        return road_coord_for_index(loop_index)

    assert grid_pos is not None
    game_map.grid[grid_pos] = tile
    return grid_pos
