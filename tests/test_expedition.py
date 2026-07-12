"""Tests for expedition resource retention."""

from game.camp.meta import CampState
from game.content.loader import ContentRegistry
from game.core.game_state import GameState
from game.models import Resources


def test_retreat_at_camp_keeps_all_resources() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.run_resources = Resources(bone_dust=10, hide=5, herb=3, metal=2)
    state.hero_loop_index = 0
    kept = state.end_expedition(at_camp=True)
    assert kept.bone_dust == 10
    # 10 bone_dust stacks into 1 hide on deposit
    assert state.camp.resources.hide == 6
    assert state.camp.resources.herb == 3
    assert state.camp.resources.metal == 2


def test_death_keeps_thirty_percent() -> None:
    content = ContentRegistry()
    state = GameState(content=content, camp=CampState())
    state.start_expedition()
    state.run_resources = Resources(bone_dust=10)
    kept = state.end_expedition(died=True)
    assert kept.bone_dust == 3
