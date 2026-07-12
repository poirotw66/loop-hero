"""Load YAML game content."""

from __future__ import annotations

from pathlib import Path

import yaml

from game.models import (
    BuildingDef,
    CardDef,
    CardType,
    ComboDef,
    EnemyDef,
    EquipmentDef,
    TraitDef,
)

CONTENT_DIR = Path(__file__).parent


def _load_yaml(name: str) -> dict:
    with open(CONTENT_DIR / name, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_cards() -> dict[str, CardDef]:
    raw = _load_yaml("cards.yaml")["cards"]
    result: dict[str, CardDef] = {}
    for item in raw:
        card = CardDef(
            id=item["id"],
            name_zh=item["name_zh"],
            card_type=CardType(item["card_type"]),
            unlock_building=item.get("unlock_building"),
            default_unlocked=item.get("default_unlocked", item.get("unlock_building") is None),
            effects=item.get("effects", {}),
        )
        result[card.id] = card
    return result


def load_enemies() -> dict[str, EnemyDef]:
    raw = _load_yaml("enemies.yaml")["enemies"]
    result: dict[str, EnemyDef] = {}
    for item in raw:
        enemy = EnemyDef(
            id=item["id"],
            name_zh=item["name_zh"],
            hp=item["hp"],
            damage=item["damage"],
            defense=item["defense"],
            attack_speed=item["attack_speed"],
            is_boss=item.get("is_boss", False),
            special=item.get("special", {}),
            loot=item.get("loot", {}),
        )
        result[enemy.id] = enemy
    return result


def load_equipment() -> dict[str, EquipmentDef]:
    raw = _load_yaml("equipment.yaml")["equipment"]
    result: dict[str, EquipmentDef] = {}
    for item in raw:
        eq = EquipmentDef(
            id=item["id"],
            name_zh=item["name_zh"],
            slot=item["slot"],
            rarity=item["rarity"],
            bonuses=item.get("bonuses", {}),
        )
        result[eq.id] = eq
    return result


def load_traits() -> dict[str, TraitDef]:
    raw = _load_yaml("traits.yaml")["traits"]
    result: dict[str, TraitDef] = {}
    for item in raw:
        trait = TraitDef(
            id=item["id"],
            name_zh=item["name_zh"],
            description_zh=item["description_zh"],
            effect_id=item["effect_id"],
        )
        result[trait.id] = trait
    return result


def load_buildings() -> dict[str, BuildingDef]:
    raw = _load_yaml("buildings.yaml")["buildings"]
    result: dict[str, BuildingDef] = {}
    for item in raw:
        building = BuildingDef(
            id=item["id"],
            name_zh=item["name_zh"],
            cost=item.get("cost", {}),
            unlocks_card=item.get("unlocks_card"),
            passive=item.get("passive", {}),
            default_built=item.get("default_built", False),
        )
        result[building.id] = building
    return result


def load_combos() -> list[ComboDef]:
    raw = _load_yaml("combos.yaml")["combos"]
    return [
        ComboDef(
            id=item["id"],
            condition=item["condition"],
            result_card=item["condition"]["result"],
            description_zh=item["description_zh"],
        )
        for item in raw
    ]


class ContentRegistry:
    """In-memory registry of all loaded content."""

    def __init__(self) -> None:
        self.cards = load_cards()
        self.enemies = load_enemies()
        self.equipment = load_equipment()
        self.traits = load_traits()
        self.buildings = load_buildings()
        self.combos = load_combos()
