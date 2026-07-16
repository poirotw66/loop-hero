"""Shared data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GameMode(str, Enum):
    ADVENTURE = "adventure"
    PLANNING = "planning"


class CardType(str, Enum):
    ROAD = "road"
    ROADSIDE = "roadside"
    LANDSCAPE = "landscape"
    SPECIAL = "special"


class ExpeditionPhase(str, Enum):
    TRAVELING = "traveling"
    COMBAT = "combat"
    LEVEL_UP = "level_up"
    ENDED = "ended"


@dataclass
class Stats:
    max_hp: float = 100.0
    hp: float = 100.0
    damage: float = 12.0
    defense: float = 6.0
    attack_speed: float = 1.0
    evasion: float = 0.08
    vampirism: float = 0.0
    counterattack: float = 0.0
    regen_per_sec: float = 0.0

    def copy(self) -> Stats:
        return Stats(
            max_hp=self.max_hp,
            hp=self.hp,
            damage=self.damage,
            defense=self.defense,
            attack_speed=self.attack_speed,
            evasion=self.evasion,
            vampirism=self.vampirism,
            counterattack=self.counterattack,
            regen_per_sec=self.regen_per_sec,
        )


@dataclass
class CardDef:
    id: str
    name_zh: str
    card_type: CardType
    unlock_building: str | None = None
    default_unlocked: bool = True
    effects: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnemyDef:
    id: str
    name_zh: str
    hp: float
    damage: float
    defense: float
    attack_speed: float
    is_boss: bool = False
    special: dict[str, Any] = field(default_factory=dict)
    loot: dict[str, Any] = field(default_factory=dict)


@dataclass
class EquipmentDef:
    id: str
    name_zh: str
    slot: str
    rarity: str
    bonuses: dict[str, float] = field(default_factory=dict)


@dataclass
class TraitDef:
    id: str
    name_zh: str
    description_zh: str
    effect_id: str


@dataclass
class BuildingDef:
    id: str
    name_zh: str
    cost: dict[str, int] = field(default_factory=dict)
    unlocks_card: str | None = None
    passive: dict[str, Any] = field(default_factory=dict)
    default_built: bool = False


@dataclass
class ComboDef:
    id: str
    condition: dict[str, Any]
    result_card: str
    description_zh: str


@dataclass
class PlacedTile:
    card_id: str
    variant: str | None = None
    spawned_enemies: list[str] = field(default_factory=list)


@dataclass
class Combatant:
    name: str
    stats: Stats
    enemy_id: str | None = None
    attack_gauge: float = 0.0
    is_hero: bool = False
    shield: float = 0.0
    boss_turns: int = 0
    boss_shield_used: bool = False
    blind_rage_used: bool = False


@dataclass
class EquipmentItem:
    def_id: str
    slot: str


@dataclass
class Resources:
    bone_dust: int = 0
    hide: int = 0
    herb: int = 0
    metal: int = 0

    def add(self, resource_id: str, amount: int) -> None:
        current = getattr(self, resource_id, 0)
        setattr(self, resource_id, current + amount)

    def get(self, resource_id: str) -> int:
        return getattr(self, resource_id, 0)

    def can_afford(self, cost: dict[str, int]) -> bool:
        return all(self.get(key) >= amount for key, amount in cost.items())

    def spend(self, cost: dict[str, int]) -> None:
        for key, amount in cost.items():
            setattr(self, key, self.get(key) - amount)

    def scaled(self, rate: float) -> Resources:
        return Resources(
            bone_dust=int(self.bone_dust * rate),
            hide=int(self.hide * rate),
            herb=int(self.herb * rate),
            metal=int(self.metal * rate),
        )

    def merge(self, other: Resources) -> None:
        self.bone_dust += other.bone_dust
        self.hide += other.hide
        self.herb += other.herb
        self.metal += other.metal
