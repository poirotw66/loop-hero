"""Headless playtest harness — simulate runs and report metrics."""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field

from game.camp.meta import CampState
from game.content.loader import ContentRegistry
from game.core.game_state import GameState
from game.core.map import is_valid_landscape, is_valid_roadside
from game.models import CardType, ExpeditionPhase, GameMode


@dataclass
class RunReport:
    seed: int
    ended_reason: str
    loops: int
    days: int
    cards_placed: int
    combats: int
    boss_spawned: bool
    boss_defeated: bool
    hp_end: float
    kept_bone: int
    kept_hide: int
    kept_herb: int
    kept_metal: int
    deaths: bool
    enemies_spawned: Counter = field(default_factory=Counter)
    notes: list[str] = field(default_factory=list)


def _try_place_any(state: GameState, rng: random.Random) -> bool:
    if not state.hand:
        return False
    card_id = state.hand[0]
    card = state.content.cards[card_id]

    if card.card_type == CardType.ROAD:
        indices = list(range(1, 8))
        rng.shuffle(indices)
        for loop_index in indices:
            if state.place_card_from_hand(card_id, loop_index=loop_index):
                return True
        # discard unusable road card to avoid softlock
        state.hand.pop(0)
        return False

    positions = [(r, c) for r in range(7) for c in range(7)]
    rng.shuffle(positions)
    for pos in positions:
        if card.card_type == CardType.ROADSIDE and not is_valid_roadside(pos[0], pos[1]):
            continue
        if card.card_type in {CardType.LANDSCAPE, CardType.SPECIAL} and not is_valid_landscape(
            pos[0], pos[1]
        ):
            continue
        if state.place_card_from_hand(card_id, grid_pos=pos):
            return True
    state.hand.pop(0)
    return False


def _count_road_enemies(state: GameState) -> Counter:
    counts: Counter = Counter()
    for tile in state.map.road_tiles:
        for enemy_id in tile.spawned_enemies:
            counts[enemy_id] += 1
    return counts


def _count_grid_enemies(state: GameState) -> Counter:
    counts: Counter = Counter()
    for tile in state.map.grid.values():
        for enemy_id in tile.spawned_enemies:
            counts[enemy_id] += 1
    return counts


def simulate_run(
    seed: int,
    *,
    max_ticks: int = 5000,
    place_every_n_tiles: int = 2,
    retreat_at_boss: bool = True,
    camp: CampState | None = None,
) -> RunReport:
    content = ContentRegistry()
    camp = camp or CampState()
    state = GameState(content=content, camp=camp, rng=random.Random(seed))
    state.start_expedition()
    state.mode = GameMode.ADVENTURE

    rng = random.Random(seed + 17)
    cards_placed = 0
    combats = 0
    boss_spawned = False
    notes: list[str] = []
    enemies_seen: Counter = Counter()
    tiles_walked = 0

    # Place starter cards in planning bursts
    state.mode = GameMode.PLANNING
    while state.hand and cards_placed < 4:
        if _try_place_any(state, rng):
            cards_placed += 1
        else:
            break
    state.mode = GameMode.ADVENTURE

    for _ in range(max_ticks):
        if state.phase == ExpeditionPhase.ENDED:
            break

        if state.phase == ExpeditionPhase.LEVEL_UP and state.pending_trait_choices:
            state.choose_trait(state.pending_trait_choices[0])

        before_index = state.hero_loop_index
        grid_before = _count_grid_enemies(state)

        # Equip each inventory item once (don't reshuffle swapped gear forever).
        state.mode = GameMode.PLANNING
        for _ in range(len(state.inventory)):
            if not state.inventory:
                break
            state.equip_item(0)
        state.mode = GameMode.ADVENTURE

        state.tick(delta=10)

        if state.combat_log:
            combats += 1
            if "虛空守衛" in "".join(state.combat_log) or state.boss_defeated_this_run:
                boss_spawned = True

        if state.boss_defeated_this_run:
            boss_spawned = True

        if state.phase == ExpeditionPhase.ENDED:
            break

        if before_index != state.hero_loop_index:
            tiles_walked += 1
            enemies_seen.update(_count_road_enemies(state))
            if (
                state.hand
                and tiles_walked % place_every_n_tiles == 0
                and state.hero_stats.hp > state.hero_stats.max_hp * 0.4
            ):
                state.mode = GameMode.PLANNING
                if _try_place_any(state, rng):
                    cards_placed += 1
                for _ in range(len(state.inventory)):
                    if not state.inventory:
                        break
                    state.equip_item(0)
                state.mode = GameMode.ADVENTURE

        if state.boss_defeated_this_run:
            boss_spawned = True

        # Detect stranded grid enemies (never fightable)
        grid_enemies = _count_grid_enemies(state)
        if grid_enemies and grid_enemies != grid_before:
            stranded = sum(grid_enemies.values())
            if stranded > 0 and "grid_enemies" not in notes:
                notes.append(f"grid_enemies_stranded={dict(grid_enemies)}")

        if state.boss_defeated_this_run and retreat_at_boss and state.hero_loop_index == 0:
            state.end_expedition(at_camp=True)
            break

        # Retreat if low HP at camp, but only before boss meter is ready.
        if (
            state.loop_count >= 2
            and state.hero_stats.hp < state.hero_stats.max_hp * 0.3
            and state.hero_loop_index == 0
            and not state.boss_pending
            and state.boss_meter < 64
        ):
            state.end_expedition(at_camp=True)
            notes.append("retreated_low_hp")
            break

        # Safety: too many loops → camp retreat
        if state.loop_count >= 20 and state.hero_loop_index == 0:
            state.end_expedition(at_camp=True)
            notes.append("retreated_timeout")
            break

    if state.phase != ExpeditionPhase.ENDED:
        state.end_expedition(at_camp=state.hero_loop_index == 0)
        notes.append("force_end")

    reason = "death" if state.last_died else "retreat"
    if state.boss_defeated_this_run:
        reason = "boss_win"
    kept = state.last_kept_resources
    return RunReport(
        seed=seed,
        ended_reason=reason,
        loops=state.loop_count,
        days=state.day_count,
        cards_placed=cards_placed,
        combats=combats,
        boss_spawned=boss_spawned or state.boss_defeated_this_run,
        boss_defeated=state.boss_defeated_this_run,
        hp_end=state.hero_stats.hp,
        kept_bone=kept.bone_dust,
        kept_hide=kept.hide,
        kept_herb=kept.herb,
        kept_metal=kept.metal,
        deaths=state.last_died,
        enemies_spawned=enemies_seen,
        notes=notes,
    )


def simulate_meta(num_runs: int = 20, seed_base: int = 100) -> dict:
    """Multiple expeditions with shared camp progression."""
    camp = CampState()
    reports: list[RunReport] = []
    for index in range(num_runs):
        report = simulate_run(seed_base + index, camp=camp)
        reports.append(report)
        # Greedy build after each run
        content = ContentRegistry()
        for building_id in ("gymnasium", "smithy", "herbalist_hut", "supply_depot"):
            if camp.can_build(content, building_id):
                camp.build(content, building_id)

    built = sorted(camp.built_buildings)
    resources = camp.resources
    return {
        "runs": reports,
        "buildings": built,
        "camp_resources": {
            "bone_dust": resources.bone_dust,
            "hide": resources.hide,
            "herb": resources.herb,
            "metal": resources.metal,
        },
        "boss_wins": sum(1 for r in reports if r.boss_defeated),
        "deaths": sum(1 for r in reports if r.deaths),
        "avg_loops": sum(r.loops for r in reports) / max(len(reports), 1),
        "avg_kept_total": sum(
            r.kept_bone + r.kept_hide + r.kept_herb + r.kept_metal for r in reports
        )
        / max(len(reports), 1),
        "stranded_grid_enemy_runs": sum(
            1 for r in reports if any(n.startswith("grid_enemies") for n in r.notes)
        ),
    }


def print_summary(meta: dict) -> None:
    print("=== PLAYTEST META ===")
    print(f"runs={len(meta['runs'])} deaths={meta['deaths']} boss_wins={meta['boss_wins']}")
    print(f"avg_loops={meta['avg_loops']:.1f} avg_kept_resources={meta['avg_kept_total']:.1f}")
    print(f"buildings={meta['buildings']}")
    print(f"camp_resources={meta['camp_resources']}")
    print(f"stranded_grid_enemy_runs={meta['stranded_grid_enemy_runs']}")
    reasons = Counter(r.ended_reason for r in meta["runs"])
    print(f"end_reasons={dict(reasons)}")
    for report in meta["runs"][:5]:
        print(
            f"  seed={report.seed} reason={report.ended_reason} "
            f"loops={report.loops} days={report.days} "
            f"cards={report.cards_placed} boss={report.boss_spawned}/{report.boss_defeated} "
            f"notes={report.notes}"
        )


if __name__ == "__main__":
    print_summary(simulate_meta(20, seed_base=42))
