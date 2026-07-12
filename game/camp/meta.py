"""Camp meta progression."""

from __future__ import annotations

from dataclasses import dataclass, field

from game.constants import RESOURCE_CHAIN, RESOURCE_STACK_SIZE
from game.content.loader import ContentRegistry
from game.models import Resources


@dataclass
class CampState:
    resources: Resources = field(default_factory=Resources)
    built_buildings: set[str] = field(default_factory=lambda: {"campfire"})
    boss_defeated: bool = False

    def unlocked_cards(self, content: ContentRegistry) -> set[str]:
        unlocked = {
            card_id
            for card_id, card in content.cards.items()
            if card.default_unlocked
        }
        for building_id in self.built_buildings:
            building = content.buildings.get(building_id)
            if building and building.unlocks_card:
                unlocked.add(building.unlocks_card)
        unlocked.update({"wasteland", "camp", "blooming_meadow", "empty_treasury", "mountain_peak", "bandit_camp", "goblin_camp"})
        return unlocked

    def can_build(self, content: ContentRegistry, building_id: str) -> bool:
        if building_id in self.built_buildings:
            return False
        building = content.buildings[building_id]
        return self.resources.can_afford(building.cost)

    def build(self, content: ContentRegistry, building_id: str) -> bool:
        if not self.can_build(content, building_id):
            return False
        building = content.buildings[building_id]
        self.resources.spend(building.cost)
        self.built_buildings.add(building_id)
        return True

    def deposit_run_resources(self, run_resources: Resources) -> None:
        stacked = _stack_resources(run_resources)
        self.resources.merge(stacked)


def _stack_resources(resources: Resources) -> Resources:
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
