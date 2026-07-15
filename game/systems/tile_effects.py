"""Tile daily and pass-by effects."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from game.core.map import adjacent_cells, road_coord_for_index, touching_cells

if TYPE_CHECKING:
    from game.core.game_state import GameState


def on_new_day(state: "GameState") -> None:
    _landscape_daily_heal(state)
    _road_daily_spawns(state)
    _grid_daily_spawns(state)
    if "blade_of_dawn" in state.hero_traits:
        state.dawn_attack_ready = True


def on_loop_complete(state: "GameState") -> None:
    state.loop_count += 1
    if "skilled_armorer" in state.hero_traits:
        state.loop_defense_bonus += 1
        state.hero_stats.defense += 1
    _battlefield_loop_rewards(state)


def on_pass_road_tile(state: "GameState", loop_index: int) -> None:
    tile = state.map.road_tile_at(loop_index)

    # Camp is a special loop anchor, not a content card.
    if loop_index == 0 or tile.card_id == "camp":
        heal = state.hero_stats.max_hp * 0.35
        state.hero_stats.hp = min(state.hero_stats.max_hp, state.hero_stats.hp + heal)
        if state.boss_pending:
            tile.spawned_enemies.append("void_warden")
            state.boss_pending = False
        return

    card = state.content.cards.get(tile.card_id)
    if card is None:
        return

    effects = card.effects
    if "heal_on_pass" in effects:
        amount = effects["heal_on_pass"]["base"] + effects["heal_on_pass"]["per_loop"] * state.loop_count
        state.hero_stats.hp = min(state.hero_stats.max_hp, state.hero_stats.hp + amount)

    if effects.get("invert_healing"):
        state.hero_stats.hp = max(0, state.hero_stats.hp - 5)


def _landscape_daily_heal(state: "GameState") -> None:
    bonus = 0
    if "herbalist_hut" in state.camp.built_buildings and not state.first_heal_bonus_used:
        bonus = 3
        state.first_heal_bonus_used = True

    for tile in state.map.grid.values():
        card = state.content.cards.get(tile.card_id)
        if card is None:
            continue
        heal = card.effects.get("daily_heal", 0)
        if heal:
            state.hero_stats.hp = min(
                state.hero_stats.max_hp,
                state.hero_stats.hp + heal + bonus,
            )
            bonus = 0


def _road_daily_spawns(state: "GameState") -> None:
    for index, tile in enumerate(state.map.road_tiles):
        card = state.content.cards.get(tile.card_id)
        if card is None:
            continue
        effects = card.effects
        if "daily_spawn" in effects:
            spawn = effects["daily_spawn"]
            if state.rng.random() < spawn.get("chance", 0):
                _append_spawn(tile, spawn["enemy"], spawn.get("max_per_tile", 99))
        if "spawn_every_days" in effects:
            spawn = effects["spawn_every_days"]
            if state.day_count % spawn["interval"] == 0:
                _append_spawn(tile, spawn["enemy"], spawn.get("max_per_tile", 99))


def _grid_daily_spawns(state: "GameState") -> None:
    for pos, tile in state.map.grid.items():
        card = state.content.cards.get(tile.card_id)
        if card is None:
            continue
        effects = card.effects
        if "spawn_every_days" in effects:
            spawn = effects["spawn_every_days"]
            if state.day_count % spawn["interval"] == 0:
                # Combat only happens on road tiles — always spawn there.
                road_index = _nearest_road_index_to_pos(pos)
                road_tile = state.map.road_tile_at(road_index)
                _append_spawn(road_tile, spawn["enemy"], spawn.get("max_per_tile", 99))
        if "adjacent_road_daily_spawn" in effects:
            spawn = effects["adjacent_road_daily_spawn"]
            row, col = pos
            for road_index, road_pos in enumerate([road_coord_for_index(i) for i in range(8)]):
                if road_pos in adjacent_cells(row, col, include_diagonal=True):
                    road_tile = state.map.road_tile_at(road_index)
                    _append_spawn(road_tile, spawn["enemy"], spawn.get("max_per_tile", 99))


def _append_spawn(tile, enemy_id: str, max_count: int) -> None:
    same = sum(1 for spawned in tile.spawned_enemies if spawned == enemy_id)
    if same < max_count:
        tile.spawned_enemies.append(enemy_id)


def _nearest_road_index(state: "GameState", from_tile) -> int | None:
    for index in range(8):
        if state.map.road_tile_at(index) is from_tile:
            return index
    return 0


def _nearest_road_index_to_pos(pos: tuple[int, int]) -> int:
    from game.core.map import manhattan

    best_index = 0
    best_distance = 10**9
    for index in range(8):
        distance = manhattan(pos, road_coord_for_index(index))
        if distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index


def _battlefield_loop_rewards(state: "GameState") -> None:
    for pos, tile in state.map.grid.items():
        if tile.card_id != "battlefield":
            continue
        row, col = pos
        for road_index, road_pos in enumerate([road_coord_for_index(i) for i in range(8)]):
            if road_pos not in touching_cells(row, col):
                continue
            if state.rng.random() < 0.5:
                road_tile = state.map.road_tile_at(road_index)
                road_tile.spawned_enemies.append("mimic")
            else:
                state.run_resources.add("metal", 1)


def recompute_passive_stats(state: "GameState") -> None:
    base = state.base_stats.copy()
    for item in state.equipped.values():
        if item is None:
            continue
        definition = state.content.equipment[item.def_id]
        for key, value in definition.bonuses.items():
            current = getattr(base, key, 0)
            setattr(base, key, current + value)

    if "smithy" in state.camp.built_buildings:
        multiplier = 1.05
        base.damage *= multiplier
        base.max_hp *= multiplier
        base.defense *= multiplier

    base.defense += state.loop_defense_bonus

    for tile in list(state.map.grid.values()):
        card = state.content.cards.get(tile.card_id)
        if card is None:
            continue
        if "max_hp_percent" in card.effects:
            base.max_hp *= 1 + card.effects["max_hp_percent"] / 100
        if "attack_speed_percent" in card.effects:
            base.attack_speed *= 1 + card.effects["attack_speed_percent"] / 100

    # Touching rock/mountain bonus
    for pos, tile in list(state.map.grid.items()):
        card = state.content.cards.get(tile.card_id)
        if card is None:
            continue
        bonus_per = card.effects.get("touching_rock_mountain_bonus")
        if not bonus_per:
            continue
        from game.core.map import touching_cells

        for neighbor in touching_cells(pos[0], pos[1]):
            other = state.map.grid.get(neighbor)
            if other and other.card_id in {"rock", "mountain", "mountain_peak"}:
                base.max_hp *= 1 + bonus_per / 100

    hp_ratio = state.hero_stats.hp / max(state.hero_stats.max_hp, 1)
    base.hp = min(base.max_hp, base.max_hp * hp_ratio)
    state.hero_stats = base
