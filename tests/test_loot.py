"""Tests for loot table coverage."""

import random

from game.content.loader import ContentRegistry
from game.systems.loot import roll_enemy_loot


def test_equipment_loot_covers_all_slots() -> None:
    content = ContentRegistry()
    slots: set[str] = set()
    rng = random.Random(0)
    for _ in range(200):
        _, equipment_id, _ = roll_enemy_loot(content, "wolf", rng)
        if equipment_id:
            slots.add(content.equipment[equipment_id].slot)
    assert slots == {"weapon", "armor", "shield", "ring"}
