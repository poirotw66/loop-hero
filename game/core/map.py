"""7x7 map and loop road representation."""

from __future__ import annotations

from game.constants import LOOP_LENGTH, MAP_SIZE, ROAD_COORDS
from game.models import PlacedTile


def road_coord_for_index(index: int) -> tuple[int, int]:
    return ROAD_COORDS[index % LOOP_LENGTH]


def is_road_cell(row: int, col: int) -> bool:
    return (row, col) in set(ROAD_COORDS)


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def is_touching_road(row: int, col: int) -> bool:
    for road in ROAD_COORDS:
        if manhattan((row, col), road) == 1:
            return True
    return False


def is_valid_landscape(row: int, col: int) -> bool:
    if not (0 <= row < MAP_SIZE and 0 <= col < MAP_SIZE):
        return False
    if is_road_cell(row, col):
        return False
    for road in ROAD_COORDS:
        if manhattan((row, col), road) <= 1:
            return False
    return True


def is_valid_roadside(row: int, col: int) -> bool:
    if not (0 <= row < MAP_SIZE and 0 <= col < MAP_SIZE):
        return False
    if is_road_cell(row, col):
        return False
    return is_touching_road(row, col)


def adjacent_cells(row: int, col: int, include_diagonal: bool = True) -> list[tuple[int, int]]:
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if include_diagonal:
        offsets.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
    cells: list[tuple[int, int]] = []
    for dr, dc in offsets:
        nr, nc = row + dr, col + dc
        if 0 <= nr < MAP_SIZE and 0 <= nc < MAP_SIZE:
            cells.append((nr, nc))
    return cells


def touching_cells(row: int, col: int) -> list[tuple[int, int]]:
    return adjacent_cells(row, col, include_diagonal=False)


class GameMap:
    """Road loop plus off-road grid placements."""

    def __init__(self) -> None:
        self.road_tiles: list[PlacedTile] = [
            PlacedTile(card_id="camp" if index == 0 else "wasteland")
            for index in range(LOOP_LENGTH)
        ]
        self.grid: dict[tuple[int, int], PlacedTile] = {}

    def road_tile_at(self, loop_index: int) -> PlacedTile:
        return self.road_tiles[loop_index % LOOP_LENGTH]

    def set_road_tile(self, loop_index: int, tile: PlacedTile) -> None:
        if loop_index == 0:
            tile = PlacedTile(card_id="camp")
        self.road_tiles[loop_index % LOOP_LENGTH] = tile

    def count_card_on_road(self, card_id: str) -> int:
        return sum(1 for tile in self.road_tiles if tile.card_id == card_id)

    def count_card_in_grid(self, card_id: str) -> int:
        return sum(1 for tile in self.grid.values() if tile.card_id == card_id)

    def count_card(self, card_id: str) -> int:
        return self.count_card_on_road(card_id) + self.count_card_in_grid(card_id)

    def rock_mountain_count(self) -> int:
        total = 0
        for tile in list(self.road_tiles) + list(self.grid.values()):
            if tile.card_id in {"rock", "mountain"}:
                total += 1
        return total
