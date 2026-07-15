"""Loot and resource helpers."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from game.constants import RESOURCE_CHAIN, RESOURCE_STACK_SIZE
from game.models import EquipmentItem, Resources

if TYPE_CHECKING:
    from game.content.loader import ContentRegistry
    from game.core.game_state import GameState


def stack_resources(resources: Resources) -> Resources:
    """Combine 10 lower-tier resources into 1 higher-tier."""
    values = [resources.get(key) for key in RESOURCE_CHAIN]
    for index in range(len(RESOURCE_CHAIN) - 1):
        while values[index] >= RESOURCE_STACK_SIZE:
            values[index] -= RESOURCE_STACK_SIZE
            values[index + 1] += 1
    return Resources(
        bone_dust=values[0],
        hide=values[1],
        herb=values[2],
        metal=values[3],
    )


def roll_enemy_loot(content: ContentRegistry, enemy_id: str, rng: random.Random) -> tuple[Resources, str | None, str | None]:
    enemy = content.enemies[enemy_id]
    loot = enemy.loot
    resources = Resources()
    for key, amount in loot.items():
        if key.endswith("_chance"):
            continue
        if isinstance(amount, int):
            resources.add(key, amount)

    equipment_id: str | None = None
    if rng.random() < loot.get("equipment_chance", 0.0):
        # Weight weapons higher so DPS keeps up with map danger.
        weapons = [item.id for item in content.equipment.values() if item.slot == "weapon"]
        others = [item.id for item in content.equipment.values() if item.slot != "weapon"]
        pool = weapons * 2 + others
        if pool:
            equipment_id = rng.choice(pool)

    card_id: str | None = None
    # Base card drop chance applies to every kill; enemy loot can raise it.
    card_chance = max(0.25, float(loot.get("card_chance", 0.0)))
    if rng.random() < card_chance:
        card_id = rng.choice(
            ["cemetery", "grove", "rock", "meadow", "mountain", "spider_cocoon", "battlefield"]
        )

    return resources, equipment_id, card_id


def add_equipment_to_inventory(state: "GameState", equipment_id: str) -> None:
    item = state.content.equipment[equipment_id]
    if len(state.inventory) >= state.inventory_max:
        state.run_resources.add("bone_dust", 1)
        state.inventory.pop(0)
    state.inventory.append(EquipmentItem(def_id=equipment_id, slot=item.slot))
