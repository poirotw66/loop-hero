"""Tests for sprites (generated + procedural) and synthesized SFX."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.ui.sfx import SoundBank, _tone
from game.ui.sprites import SpriteAtlas, make_enemy_sprite, make_hero_sprite, make_tile_sprite


def setup_module() -> None:
    pygame.init()
    try:
        pygame.display.set_mode((1, 1))
    except pygame.error:
        pass
    try:
        pygame.mixer.init()
    except pygame.error:
        pass


def test_tile_sprite_has_pixels() -> None:
    surface = make_tile_sprite("meadow", 32)
    assert surface.get_width() == 32
    assert surface.get_height() == 32
    assert surface.get_at((16, 16)).a > 0 or any(
        surface.get_at((x, y)).a > 0 for x in range(32) for y in range(32)
    )


def test_hero_and_enemy_sprites() -> None:
    hero = make_hero_sprite(24)
    enemy = make_enemy_sprite("void_warden", 28)
    assert hero.get_size() == (24, 24)
    assert enemy.get_size() == (28, 28)


def test_sprite_atlas_caches() -> None:
    atlas = SpriteAtlas()
    first = atlas.tile("rock", 40)
    second = atlas.tile("rock", 40)
    assert first is second


def test_sprite_atlas_loads_generated_assets() -> None:
    atlas = SpriteAtlas()
    assert atlas.has_asset("hero")
    assert atlas.has_asset("meadow")
    assert atlas.has_asset("void_warden")
    assert atlas.hero(32).get_size() == (32, 32)
    assert atlas.tile("meadow", 40).get_size() == (40, 40)
    assert atlas.enemy("slime", 28).get_size() == (28, 28)


def test_tone_and_soundbank_play() -> None:
    sound = _tone(440, 0.05, volume=0.1)
    assert sound.get_length() > 0
    bank = SoundBank()
    bank.play("place")
    bank.play("click")
