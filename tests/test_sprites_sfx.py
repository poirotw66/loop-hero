"""Tests for procedural sprites and synthesized SFX."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.ui.sfx import SoundBank, _tone
from game.ui.sprites import SpriteAtlas, make_enemy_sprite, make_hero_sprite, make_tile_sprite


def setup_module() -> None:
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error:
        pass


def test_tile_sprite_has_pixels() -> None:
    surface = make_tile_sprite("meadow", 32)
    assert surface.get_width() == 32
    assert surface.get_height() == 32
    # Not fully transparent.
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


def test_tone_and_soundbank_play() -> None:
    sound = _tone(440, 0.05, volume=0.1)
    assert sound.get_length() > 0
    bank = SoundBank()
    # Should not raise even if mixer is unavailable.
    bank.play("place")
    bank.play("click")
