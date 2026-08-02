"""Expedition orchestration and game state."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from game.camp.meta import CampState
from game.constants import (
    BOSS_METER_PER_CARD,
    CAMP_LOOP_INDEX,
    DAY_DURATION_TICKS,
    INVENTORY_MAX,
    RETREAT_RATE_CAMP,
    RETREAT_RATE_DEATH,
    RETREAT_RATE_NORMAL,
    XP_PER_LEVEL,
)
from game.content.loader import ContentRegistry
from game.core.combat import Combatant, run_combat
from game.core.map import GameMap
from game.models import (
    ChapterDef,
    EquipmentItem,
    ExpeditionPhase,
    GameMode,
    Resources,
    Stats,
)
from game.systems.combo_resolver import resolve_combos
from game.systems.loot import add_equipment_to_inventory, roll_enemy_loot
from game.systems.placement import place_card
from game.systems.tile_effects import on_loop_complete, on_new_day, on_pass_road_tile, recompute_passive_stats


@dataclass
class GameState:
    content: ContentRegistry
    camp: CampState = field(default_factory=CampState)
    rng: random.Random = field(default_factory=lambda: random.Random())

    mode: GameMode = GameMode.PLANNING
    phase: ExpeditionPhase = ExpeditionPhase.TRAVELING
    map: GameMap = field(default_factory=GameMap)
    chapter_id: str = "chapter_1"

    loop_count: int = 0
    day_count: int = 1
    day_progress: float = 0.0
    hero_loop_index: int = 0
    travel_progress: float = 0.0

    base_stats: Stats = field(default_factory=Stats)
    hero_stats: Stats = field(default_factory=Stats)
    hero_traits: list[str] = field(default_factory=list)
    hero_xp: int = 0
    hero_level: int = 1

    hand: list[str] = field(default_factory=list)
    inventory: list[EquipmentItem] = field(default_factory=list)
    equipped: dict[str, EquipmentItem | None] = field(
        default_factory=lambda: {"weapon": None, "armor": None, "shield": None, "ring": None}
    )

    run_resources: Resources = field(default_factory=Resources)
    boss_meter: float = 0.0
    boss_pending: bool = False
    boss_defeated_this_run: bool = False

    combat_log: list[str] = field(default_factory=list)
    last_combat_enemies: list[str] = field(default_factory=list)
    last_place_pos: tuple[int, int] | None = None
    pending_trait_choices: list[str] = field(default_factory=list)
    dawn_attack_ready: bool = False
    first_heal_bonus_used: bool = False
    messages: list[str] = field(default_factory=list)
    loop_defense_bonus: float = 0.0

    # Last expedition summary for result screen
    last_kept_resources: Resources = field(default_factory=Resources)
    last_retreat_rate: float = 0.0
    last_died: bool = False

    @property
    def chapter(self) -> ChapterDef:
        return self.content.chapters.get(self.chapter_id, self.content.chapters["chapter_1"])

    @property
    def boss_meter_max(self) -> float:
        return self.chapter.boss_meter_max

    @property
    def inventory_max(self) -> int:
        bonus = 0
        if "supply_depot" in self.camp.built_buildings:
            bonus = 2
        return INVENTORY_MAX + bonus

    def start_expedition(self, chapter_id: str | None = None) -> None:
        if chapter_id is not None:
            if not self.camp.chapter_unlocked(self.content, chapter_id):
                chapter_id = "chapter_1"
            self.chapter_id = chapter_id
        self.mode = GameMode.PLANNING
        self.phase = ExpeditionPhase.TRAVELING
        self.map = GameMap()
        self.loop_count = 0
        self.day_count = 1
        self.day_progress = 0.0
        self.hero_loop_index = 0
        self.travel_progress = 0.0
        self.run_resources = Resources()
        self.boss_meter = 0.0
        self.boss_pending = False
        self.boss_defeated_this_run = False
        self.combat_log = []
        self.last_combat_enemies = []
        self.last_place_pos = None
        self.pending_trait_choices = []
        self.inventory = []
        self.equipped = {"weapon": None, "armor": None, "shield": None, "ring": None}
        self.hero_traits = []
        self.hero_xp = 0
        self.hero_level = 1
        self.first_heal_bonus_used = False
        self.loop_defense_bonus = 0.0

        start_hp_bonus = 0
        if "gymnasium" in self.camp.built_buildings:
            start_hp_bonus = 10
        self.base_stats = Stats(max_hp=100 + start_hp_bonus, hp=100 + start_hp_bonus)
        self.hero_stats = self.base_stats.copy()
        recompute_passive_stats(self)

        unlocked = self.camp.unlocked_cards(self.content)
        starter = ["cemetery", "grove", "spider_cocoon", "rock", "rock", "meadow"]
        self.hand = [card for card in starter if card in unlocked]
        for card_id in self.chapter.starter_extra_cards:
            if card_id in self.content.cards:
                self.hand.append(card_id)
        # Seed a starter weapon so first boss attempts are not naked DPS.
        self.inventory.append(EquipmentItem(def_id="rusty_sword", slot="weapon"))
        self.equip_item(0)

    def toggle_mode(self) -> None:
        if self.phase == ExpeditionPhase.COMBAT:
            return
        if self.mode == GameMode.ADVENTURE:
            self.mode = GameMode.PLANNING
        else:
            self.mode = GameMode.ADVENTURE

    def place_card_from_hand(self, card_id: str, *, loop_index: int | None = None, grid_pos: tuple[int, int] | None = None) -> bool:
        if self.mode != GameMode.PLANNING:
            return False
        if card_id not in self.hand:
            return False
        try:
            placed_at = place_card(self.content, self.map, card_id, loop_index=loop_index, grid_pos=grid_pos)
        except Exception:
            return False
        self.hand.remove(card_id)
        self.last_place_pos = placed_at
        card = self.content.cards.get(card_id)
        meter_max = self.boss_meter_max
        if card and "boss_meter_delta" in card.effects:
            self.boss_meter = max(0.0, min(meter_max, self.boss_meter + card.effects["boss_meter_delta"]))
        else:
            self.boss_meter = min(meter_max, self.boss_meter + BOSS_METER_PER_CARD)
        if self.boss_meter >= meter_max:
            self.boss_pending = True
        combos = resolve_combos(self.content, self.map)
        if combos:
            self.messages.extend(combos)
        if card and card.effects.get("adjacent_place_reward") == "random_resource":
            resource = self.rng.choice(["bone_dust", "hide", "herb", "metal"])
            self.run_resources.add(resource, 1)
        recompute_passive_stats(self)
        return True

    def tick(self, delta: float = 1.0) -> None:
        if self.mode != GameMode.ADVENTURE or self.phase != ExpeditionPhase.TRAVELING:
            return

        self.travel_progress += delta
        if self.travel_progress < 10:
            return
        self.travel_progress = 0.0

        previous_index = self.hero_loop_index
        self.hero_loop_index = (self.hero_loop_index + 1) % 8
        if previous_index == 7 and self.hero_loop_index == 0:
            on_loop_complete(self)

        on_pass_road_tile(self, self.hero_loop_index)
        road_tile = self.map.road_tile_at(self.hero_loop_index)
        if road_tile.spawned_enemies:
            enemies = list(road_tile.spawned_enemies)
            road_tile.spawned_enemies.clear()
            enemies = self._apply_enemy_cap(enemies)
            if enemies:
                self._start_combat(enemies)
            return

        self.day_progress += delta
        if self.day_progress >= DAY_DURATION_TICKS:
            self.day_progress = 0.0
            self.day_count += 1
            on_new_day(self)

    def _apply_enemy_cap(self, enemies: list[str]) -> list[str]:
        """Road lantern / watch_post reduce max enemies on adjacent tiles (min 1)."""
        from game.core.map import adjacent_cells, road_coord_for_index

        cap_delta = 0
        road_pos = road_coord_for_index(self.hero_loop_index)
        for pos, tile in self.map.grid.items():
            card = self.content.cards.get(tile.card_id)
            if card is None:
                continue
            delta = card.effects.get("adjacent_road_enemy_cap_delta")
            if not delta:
                continue
            if road_pos in adjacent_cells(pos[0], pos[1], include_diagonal=True):
                cap_delta += delta
        if not enemies:
            return enemies
        cap = max(1, len(enemies) + cap_delta)
        return enemies[:cap]

    def _enemy_hp_multiplier(self) -> float:
        multiplier = 1.0
        for tile in self.map.grid.values():
            card = self.content.cards.get(tile.card_id)
            if card is None:
                continue
            if "enemy_max_hp_percent" in card.effects:
                multiplier *= 1 + card.effects["enemy_max_hp_percent"] / 100
        return multiplier

    def _start_combat(self, enemy_ids: list[str]) -> None:
        self.phase = ExpeditionPhase.COMBAT
        hero = Combatant(name="英雄", stats=self.hero_stats.copy(), is_hero=True)
        extra: list[str] = []
        for pos, tile in self.map.grid.items():
            if tile.card_id == "vampire_mansion":
                from game.core.map import road_coord_for_index, touching_cells

                road_pos = road_coord_for_index(self.hero_loop_index)
                if road_pos in touching_cells(pos[0], pos[1]):
                    extra.append("vampire")
        enemy_ids = enemy_ids + extra
        self.last_combat_enemies = list(enemy_ids)
        result = run_combat(
            self.content,
            hero,
            enemy_ids,
            self.rng,
            self.loop_count,
            self.hero_traits,
            hp_scale=self.chapter.enemy_hp_scale,
            enemy_hp_multiplier=self._enemy_hp_multiplier(),
        )
        self.hero_stats.hp = hero.stats.hp
        self.combat_log = result.log[-6:]
        if result.victory:
            for enemy_id in enemy_ids:
                enemy_def = self.content.enemies.get(enemy_id)
                if enemy_def and enemy_def.is_boss:
                    self.boss_defeated_this_run = True
                    self.messages.append(f"{enemy_def.name_zh}已擊敗！返回營火撤退可保存全部資源")
                loot, equipment_id, card_id = roll_enemy_loot(self.content, enemy_id, self.rng)
                self.run_resources.merge(loot)
                if equipment_id:
                    add_equipment_to_inventory(self, equipment_id)
                if card_id and card_id in self.camp.unlocked_cards(self.content):
                    self.hand.append(card_id)
                self.hero_xp += 20
            self._check_level_up()
        else:
            self.end_expedition(died=True)
            return
        self.phase = ExpeditionPhase.TRAVELING

    def _check_level_up(self) -> None:
        while self.hero_xp >= XP_PER_LEVEL:
            self.hero_xp -= XP_PER_LEVEL
            self.hero_level += 1
            if "gymnasium" not in self.camp.built_buildings:
                continue
            pool = [trait.id for trait in self.content.traits.values() if trait.id not in self.hero_traits]
            if len(pool) >= 3:
                self.pending_trait_choices = self.rng.sample(pool, 3)
            elif pool:
                self.pending_trait_choices = pool
            self.phase = ExpeditionPhase.LEVEL_UP

    def choose_trait(self, trait_id: str) -> None:
        if trait_id not in self.pending_trait_choices:
            return
        self.hero_traits.append(trait_id)
        self.pending_trait_choices = []
        self.phase = ExpeditionPhase.TRAVELING

    def equip_item(self, inventory_index: int) -> None:
        if inventory_index < 0 or inventory_index >= len(self.inventory):
            return
        item = self.inventory.pop(inventory_index)
        previous = self.equipped.get(item.slot)
        if previous is not None:
            self.inventory.append(previous)
        self.equipped[item.slot] = item
        recompute_passive_stats(self)

    def end_expedition(self, *, died: bool = False, at_camp: bool = False) -> Resources:
        if died:
            rate = RETREAT_RATE_DEATH
        elif at_camp or self.hero_loop_index == CAMP_LOOP_INDEX:
            rate = RETREAT_RATE_CAMP
        else:
            rate = RETREAT_RATE_NORMAL
        kept = self.run_resources.scaled(rate)
        self.camp.deposit_run_resources(kept)
        if self.boss_defeated_this_run:
            self.camp.boss_defeated = True
        self.last_kept_resources = kept
        self.last_retreat_rate = rate
        self.last_died = died
        self.phase = ExpeditionPhase.ENDED
        self.messages.append(f"遠征結束，保留 {int(rate * 100)}% 資源")
        return kept

    def build_camp(self, building_id: str) -> bool:
        return self.camp.build(self.content, building_id)
