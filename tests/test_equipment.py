"""Tests for equipment system."""

from game.camp.meta import CampState
from game.content.loader import ContentRegistry
from game.core.game_state import GameState


def test_equip_item_applies_stats() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    base_damage = state.hero_stats.damage
    from game.models import EquipmentItem

    state.inventory.append(EquipmentItem(def_id="rusty_sword", slot="weapon"))
    state.equip_item(0)
    assert state.equipped["weapon"] is not None
    assert state.hero_stats.damage == base_damage + 8
    assert len(state.inventory) == 0


def test_equip_swaps_previous_item_to_inventory() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    from game.models import EquipmentItem

    state.inventory.append(EquipmentItem(def_id="rusty_sword", slot="weapon"))
    state.equip_item(0)
    state.inventory.append(EquipmentItem(def_id="void_blade", slot="weapon"))
    state.equip_item(0)
    assert state.equipped["weapon"].def_id == "void_blade"
    assert any(item.def_id == "rusty_sword" for item in state.inventory)
