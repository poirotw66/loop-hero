"""Automatic combat resolution."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from game.content.loader import ContentRegistry
from game.models import Combatant, Stats


@dataclass
class CombatResult:
    victory: bool
    log: list[str] = field(default_factory=list)


def apply_damage(attacker: Combatant, defender: Combatant, multiplier: float, rng: random.Random) -> float:
    if rng.random() < defender.stats.evasion:
        return 0.0
    raw = max(1.0, attacker.stats.damage * multiplier - defender.stats.defense * 0.5)
    if defender.shield > 0:
        absorbed = min(defender.shield, raw)
        defender.shield -= absorbed
        raw -= absorbed
    defender.stats.hp -= raw
    if attacker.stats.vampirism > 0:
        heal = raw * attacker.stats.vampirism
        attacker.stats.hp = min(attacker.stats.max_hp, attacker.stats.hp + heal)
    return raw


def run_combat(
    content: ContentRegistry,
    hero: Combatant,
    enemy_ids: list[str],
    rng: random.Random,
    loop_count: int,
    trait_ids: list[str],
    *,
    hp_scale: float = 1.02,
    enemy_hp_multiplier: float = 1.0,
) -> CombatResult:
    enemies = [
        _spawn_enemy(content, enemy_id, loop_count, hp_scale=hp_scale, enemy_hp_multiplier=enemy_hp_multiplier)
        for enemy_id in enemy_ids
    ]
    log: list[str] = []
    dawn_bonus = "blade_of_dawn" in trait_ids
    hero_dawn_ready = dawn_bonus

    tick = 0
    while hero.stats.hp > 0 and any(enemy.stats.hp > 0 for enemy in enemies):
        tick += 1
        living_enemies = [enemy for enemy in enemies if enemy.stats.hp > 0]

        for actor in [hero] + living_enemies:
            if actor.stats.hp <= 0:
                continue
            actor.attack_gauge += actor.stats.attack_speed
            while actor.attack_gauge >= 1.0:
                actor.attack_gauge -= 1.0
                if actor is hero:
                    _hero_attack(hero, living_enemies, trait_ids, rng, log, hero_dawn_ready)
                    hero_dawn_ready = False
                else:
                    _enemy_attack(actor, hero, content, rng, log, trait_ids)
                living_enemies = [enemy for enemy in enemies if enemy.stats.hp > 0]
                if hero.stats.hp <= 0 or not living_enemies:
                    break
            if hero.stats.hp <= 0 or not living_enemies:
                break

        for enemy in enemies:
            if enemy.stats.hp <= 0 or not enemy.enemy_id:
                continue
            definition = content.enemies.get(enemy.enemy_id)
            if definition is None or not definition.is_boss:
                continue
            _tick_boss_special(enemy, hero, definition.special, log)

        if tick > 5000:
            log.append("戰鬥超時")
            break

    victory = hero.stats.hp > 0 and all(enemy.stats.hp <= 0 for enemy in enemies)
    return CombatResult(victory=victory, log=log)


def _tick_boss_special(enemy: Combatant, hero: Combatant, special: dict, log: list[str]) -> None:
    enemy.boss_turns += 1
    interval = special.get("void_pulse_interval")
    if interval and enemy.boss_turns % interval == 0:
        hero.stats.hp -= special.get("void_pulse_damage", 0)
        log.append(f"{enemy.name}發動虛空震盪！")
    threshold_ratio = special.get("shield_threshold")
    if threshold_ratio is None or enemy.boss_shield_used:
        return
    if enemy.stats.hp <= enemy.stats.max_hp * threshold_ratio:
        enemy.shield = special.get("shield_amount", 0)
        enemy.boss_shield_used = True
        log.append(f"{enemy.name}展開護盾！")


def _spawn_enemy(
    content: ContentRegistry,
    enemy_id: str,
    loop_count: int,
    *,
    hp_scale: float = 1.02,
    enemy_hp_multiplier: float = 1.0,
) -> Combatant:
    definition = content.enemies[enemy_id]
    scale = (hp_scale ** max(0, loop_count - 1)) * enemy_hp_multiplier
    stats = Stats(
        max_hp=definition.hp * scale,
        hp=definition.hp * scale,
        damage=definition.damage,
        defense=definition.defense,
        attack_speed=definition.attack_speed,
    )
    return Combatant(name=definition.name_zh, stats=stats, enemy_id=enemy_id)


def _hero_attack(
    hero: Combatant,
    enemies: list[Combatant],
    trait_ids: list[str],
    rng: random.Random,
    log: list[str],
    dawn_ready: bool,
) -> None:
    if not enemies:
        return
    target = enemies[0]
    multiplier = 1.0
    if dawn_ready:
        multiplier = 2.0
        log.append("破曉之刃！")
    if "lightning_fast" in trait_ids and rng.random() < 0.2:
        for _ in range(3):
            apply_damage(hero, target, 0.5, rng)
        log.append("雷電快攻！")
        return
    if "lethal_weakness" in trait_ids:
        missing = 1.0 - hero.stats.hp / hero.stats.max_hp
        if rng.random() < (missing / 0.1) * 0.005:
            target.stats.hp = 0
            log.append("致命弱點觸發！")
            return
    if "blind_rage" in trait_ids and not hero.blind_rage_used:
        if hero.stats.hp / hero.stats.max_hp < 0.2:
            hero.blind_rage_used = True
            for _ in range(4):
                apply_damage(hero, target, 1.0, rng)
            log.append("盲怒！")
            return
    apply_damage(hero, target, multiplier, rng)


def _enemy_attack(
    enemy: Combatant,
    hero: Combatant,
    content: ContentRegistry,
    rng: random.Random,
    log: list[str],
    trait_ids: list[str],
) -> None:
    evasion = hero.stats.evasion
    if "survivalist" in trait_ids and hero.stats.hp / hero.stats.max_hp < 0.3:
        evasion += 0.15
    original = hero.stats.evasion
    hero.stats.evasion = min(0.95, evasion)
    damage = apply_damage(enemy, hero, 1.0, rng)
    hero.stats.evasion = original
    if damage == 0 and "somersault" in trait_ids and rng.random() < 0.35:
        apply_damage(hero, enemy, 1.0, rng)
        log.append("翻滾反擊！")
    if damage > 0 and "shield_master" in trait_ids and rng.random() < 0.1:
        log.append("盾精通暈眩！")

    if enemy.enemy_id:
        special = content.enemies[enemy.enemy_id].special
        if damage > 0 and special.get("vampirism"):
            enemy.stats.hp = min(enemy.stats.max_hp, enemy.stats.hp + damage * special["vampirism"])
