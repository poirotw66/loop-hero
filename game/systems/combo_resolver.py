"""Tile combo resolution after placement."""

from __future__ import annotations

from game.content.loader import ContentRegistry
from game.core.map import GameMap, adjacent_cells, is_valid_roadside, touching_cells
from game.models import PlacedTile


def resolve_combos(content: ContentRegistry, game_map: GameMap) -> list[str]:
    triggered: list[str] = []
    triggered.extend(_combo_meadow(game_map))
    triggered.extend(_combo_mountain_peak(game_map))
    triggered.extend(_combo_treasury(game_map))
    triggered.extend(_combo_bandit_camp(content, game_map))
    triggered.extend(_combo_goblin_camp(game_map))
    return triggered


def _combo_meadow(game_map: GameMap) -> list[str]:
    results: list[str] = []
    for pos, tile in list(game_map.grid.items()):
        if tile.card_id != "meadow":
            continue
        row, col = pos
        for neighbor in touching_cells(row, col):
            other = game_map.grid.get(neighbor)
            if other is None:
                continue
            if other.card_id not in {"meadow", "blooming_meadow"}:
                game_map.grid[pos] = PlacedTile(card_id="blooming_meadow")
                results.append("COMBO-01")
                break
    return results


def _combo_mountain_peak(game_map: GameMap) -> list[str]:
    results: list[str] = []
    rock_positions = [
        pos
        for pos, tile in game_map.grid.items()
        if tile.card_id in {"rock", "mountain"}
    ]
    if len(rock_positions) < 9:
        return results

    by_row: dict[int, list[tuple[int, int]]] = {}
    for row, col in rock_positions:
        by_row.setdefault(row, []).append((row, col))

    for row in by_row:
        cols = sorted(col for _, col in by_row[row])
        for start_col in range(min(cols), max(cols) - 1):
            block = {(row + dr, start_col + dc) for dr in range(3) for dc in range(3)}
            if len(block) != 9:
                continue
            if not all(
                game_map.grid.get(pos) is not None
                and game_map.grid[pos].card_id in {"rock", "mountain"}
                for pos in block
            ):
                continue
            center = (row + 1, start_col + 1)
            for pos in block:
                if pos != center and pos in game_map.grid:
                    del game_map.grid[pos]
            game_map.grid[center] = PlacedTile(card_id="mountain_peak")
            results.append("COMBO-02")
            return results
    return results


def _combo_treasury(game_map: GameMap) -> list[str]:
    results: list[str] = []
    for pos, tile in list(game_map.grid.items()):
        if tile.card_id != "treasury":
            continue
        row, col = pos
        neighbors = adjacent_cells(row, col, include_diagonal=True)
        if len(neighbors) < 8:
            continue
        if all(neighbor in game_map.grid for neighbor in neighbors):
            game_map.grid[pos] = PlacedTile(card_id="empty_treasury")
            results.append("COMBO-03")
    return results


def _combo_bandit_camp(content: ContentRegistry, game_map: GameMap) -> list[str]:
    if game_map.count_card_on_road("village") < 2:
        return []
    if game_map.count_card_in_grid("bandit_camp") > 0:
        return []

    village_indices = [
        index for index, tile in enumerate(game_map.road_tiles) if tile.card_id == "village"
    ]
    if not village_indices:
        return []

    anchor = village_indices[0]
    from game.core.map import road_coord_for_index

    road_pos = road_coord_for_index(anchor)
    candidates = [
        pos
        for pos in adjacent_cells(road_pos[0], road_pos[1], include_diagonal=False)
        if is_valid_roadside(pos[0], pos[1]) and pos not in game_map.grid
    ]
    if not candidates:
        return []
    game_map.grid[candidates[0]] = PlacedTile(card_id="bandit_camp")
    return ["COMBO-04"]


def _combo_goblin_camp(game_map: GameMap) -> list[str]:
    if game_map.rock_mountain_count() < 10:
        return []
    if game_map.count_card_in_grid("goblin_camp") > 0:
        return []

    for pos in list(game_map.grid.keys()):
        row, col = pos
        if game_map.grid[pos].card_id not in {"rock", "mountain"}:
            continue
        for neighbor in adjacent_cells(row, col, include_diagonal=False):
            if neighbor in game_map.grid:
                continue
            if is_valid_roadside(neighbor[0], neighbor[1]):
                game_map.grid[neighbor] = PlacedTile(card_id="goblin_camp")
                return ["goblin_camp_spawn"]
    return []
