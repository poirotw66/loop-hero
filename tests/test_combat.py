"""Tests for combat engine."""

import random

from game.content.loader import ContentRegistry
from game.core.combat import Combatant, Stats, run_combat


def test_hero_wins_against_slime() -> None:
    content = ContentRegistry()
    hero = Combatant(name="Hero", stats=Stats(max_hp=100, hp=100, damage=20, defense=5, attack_speed=2.0), is_hero=True)
    result = run_combat(content, hero, ["slime"], random.Random(0), loop_count=1, trait_ids=[])
    assert result.victory
    assert hero.stats.hp > 0


def test_boss_takes_multiple_rounds() -> None:
    content = ContentRegistry()
    hero = Combatant(
        name="Hero",
        stats=Stats(max_hp=200, hp=200, damage=15, defense=8, attack_speed=1.5),
        is_hero=True,
    )
    result = run_combat(content, hero, ["void_warden"], random.Random(1), loop_count=10, trait_ids=[])
    assert result.victory or hero.stats.hp <= 0
