"""Procedural pixel sprites (agent-sprite-forge is empty — generate in-engine)."""

from __future__ import annotations

import pygame

from game.ui.theme import CARD_COLORS, ENEMY_COLORS

# ponytail: hand-tuned 16x16 patterns; swap for real art when forge is ready


def _px(size: int, pixels: list[str], palette: dict[str, tuple[int, int, int]]) -> pygame.Surface:
    """Build a scaled surface from ASCII pixel rows."""
    height = len(pixels)
    width = len(pixels[0]) if pixels else 0
    raw = pygame.Surface((width, height), pygame.SRCALPHA)
    for y, row in enumerate(pixels):
        for x, ch in enumerate(row):
            if ch == "." or ch not in palette:
                continue
            raw.set_at((x, y), palette[ch])
    return pygame.transform.scale(raw, (size, size))


def make_hero_sprite(size: int = 24) -> pygame.Surface:
    return _px(
        size,
        [
            "................",
            "......HHHH......",
            ".....HssssH.....",
            ".....Hs..sH.....",
            "......HHHH......",
            ".....BBBBBB.....",
            "....B.BBBB.B....",
            "....B.BBBB.B....",
            ".....BBBBBB.....",
            "......B..B......",
            "......L..L......",
            "......L..L......",
            ".....LL..LL.....",
            "................",
            "................",
            "................",
        ],
        {
            "H": (60, 50, 40),
            "s": (220, 180, 140),
            "B": (70, 130, 200),
            "L": (40, 50, 90),
        },
    )


def make_tile_sprite(card_id: str, size: int = 40) -> pygame.Surface:
    base = CARD_COLORS.get(card_id, (80, 80, 90))
    light = tuple(min(255, c + 40) for c in base)
    dark = tuple(max(0, c - 40) for c in base)
    accent = (255, 220, 100)

    patterns: dict[str, list[str]] = {
        "camp": [
            "................",
            ".......aa.......",
            "......aaaa......",
            ".....aaaaaa.....",
            "....aaaaaaaa....",
            "......dddd......",
            ".....dddddd.....",
            "....dddddddd....",
            "...dddddddddd...",
            "....bb....bb....",
            "....bb....bb....",
            "...bbbbbbbbbb...",
            "..bbbbbbbbbbbb..",
            "................",
            "................",
            "................",
        ],
        "meadow": [
            "................",
            "................",
            "....g..g..g.....",
            "...gg.gg.gg.g...",
            "..ggggggggggg...",
            ".ggggggggggggg..",
            ".ggggggggggggg..",
            "..ggggggggggg...",
            "...f..f..f......",
            "....f..f........",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "blooming_meadow": [
            "................",
            "...p..y..p......",
            "....g..g..g.....",
            "...ggpgggygg....",
            "..ggggggggggg...",
            ".gggpgggyggggg..",
            ".ggggggggggggg..",
            "..gggygggpggg...",
            "...y..p..y......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "rock": [
            "................",
            "......ddd.......",
            "....ddddddd.....",
            "...ddddddddd....",
            "..ddddldddddd...",
            "..ddddddddddd...",
            "...ddddddddd....",
            "....ddddddd.....",
            ".....ddddd......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "mountain": [
            "................",
            ".......l........",
            "......lll.......",
            ".....dllld......",
            "....ddddddd.....",
            "...ddddddddd....",
            "..ddddddddddd...",
            ".ddddddddddddd..",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "mountain_peak": [
            "................",
            ".......w........",
            "......www.......",
            ".....lwlwl......",
            "....dllllld.....",
            "...ddddddddd....",
            "..ddddddddddd...",
            ".ddddddddddddd..",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "cemetery": [
            "................",
            "......lll.......",
            "......lll.......",
            ".....lllll......",
            "....lllllll.....",
            "......ddd.......",
            ".....ddddd......",
            "....ddddddd.....",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "grove": [
            "................",
            ".....ggggg......",
            "....ggggggg.....",
            "...ggggggggg....",
            "....gggbggg.....",
            "......bbb.......",
            "......bbb.......",
            ".....bbbbb......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "forest": [
            "................",
            "...ggg...ggg....",
            "..ggggg.ggggg...",
            ".ggggggggggggg..",
            "..gggbgggggbgg..",
            "....bbb...bbb...",
            "....bbb...bbb...",
            "...bbbbb.bbbbb..",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "spider_cocoon": [
            "................",
            ".....wwwww......",
            "....wwlwlww.....",
            "...wwwwwwwww....",
            "...wwlwlwlww....",
            "....wwwwwww.....",
            ".....wwwww......",
            "......www.......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "vampire_mansion": [
            "................",
            "....r..r..r.....",
            "...rrrrrrrrr....",
            "...rdrdrdrdr....",
            "...rrrrrrrrr....",
            "...r.r.r.r.r....",
            "...rrrrrrrrr....",
            "...ddddddddd....",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "road_lantern": [
            "................",
            "......aaa.......",
            ".....aaaaa......",
            "......lll.......",
            "......lll.......",
            "......ddd.......",
            ".....ddddd......",
            "......ddd.......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "treasury": [
            "................",
            "....aaaaaaa.....",
            "...aaaaaaaaa....",
            "...aadadaada....",
            "...aaaaaaaaa....",
            "...aadadaada....",
            "...aaaaaaaaa....",
            "....ddddddd.....",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "village": [
            "................",
            ".....aaaa.......",
            "....aaaaaa......",
            "...aaaaaaaa.....",
            "...aaddaadda....",
            "...aaaaaaaaa....",
            "...ddddddddd....",
            "....ddddddd.....",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
    }

    pixels = patterns.get(
        card_id,
        [
            "................",
            "....dddddddd....",
            "...dddddddddd...",
            "...ddllddlldd...",
            "...dddddddddd...",
            "...ddllddlldd...",
            "...dddddddddd...",
            "....dddddddd....",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
    )
    return _px(
        size,
        pixels,
        {
            "a": accent,
            "d": dark,
            "l": light,
            "g": base if card_id.startswith("meadow") or "grove" in card_id or "forest" in card_id else (50, 120, 50),
            "b": (90, 60, 30),
            "f": (220, 80, 120),
            "p": (220, 80, 160),
            "y": (240, 220, 80),
            "w": (230, 230, 240),
            "r": (140, 40, 50),
        },
    )


def make_enemy_sprite(enemy_id: str, size: int = 28) -> pygame.Surface:
    base = ENEMY_COLORS.get(enemy_id, (160, 80, 80))
    light = tuple(min(255, c + 50) for c in base)
    dark = tuple(max(0, c - 50) for c in base)
    patterns: dict[str, list[str]] = {
        "slime": [
            "................",
            "................",
            ".....lllll......",
            "....lllllll.....",
            "...llleellll....",
            "...lllllllll....",
            "....lllllll.....",
            ".....lllll......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "wolf": [
            "................",
            "...e............",
            "..eee..ddd......",
            ".eedeeedddd.....",
            "..eeddddddd.....",
            "...dddddddd.....",
            "....dd..dd......",
            "....d....d......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "skeleton": [
            "................",
            ".....wwwww......",
            "....ww.e.ww.....",
            ".....wwwww......",
            "......www.......",
            ".....wwwww......",
            "....w.www.w.....",
            "......w.w.......",
            ".....ww.ww......",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
        "void_warden": [
            "................",
            "......ppp.......",
            ".....ppppp......",
            "....pp.e.pp.....",
            "....ppppppp.....",
            "...ppppppppp....",
            "...pp.ppp.pp....",
            "....pp...pp.....",
            "...ppp...ppp....",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
    }
    pixels = patterns.get(
        enemy_id,
        [
            "................",
            ".....ddddd......",
            "....ddddddd.....",
            "...dd.e.e.dd....",
            "...ddddddddd....",
            "....ddddddd.....",
            ".....d...d......",
            "....dd...dd.....",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
            "................",
        ],
    )
    return _px(
        size,
        pixels,
        {
            "d": dark,
            "l": light,
            "e": (20, 20, 20),
            "w": (230, 230, 220),
            "p": (90, 60, 180),
        },
    )


class SpriteAtlas:
    """Lazy-cached procedural sprites."""

    def __init__(self) -> None:
        self._tiles: dict[tuple[str, int], pygame.Surface] = {}
        self._enemies: dict[tuple[str, int], pygame.Surface] = {}
        self._hero: dict[int, pygame.Surface] = {}

    def tile(self, card_id: str, size: int = 40) -> pygame.Surface:
        key = (card_id, size)
        if key not in self._tiles:
            self._tiles[key] = make_tile_sprite(card_id, size)
        return self._tiles[key]

    def enemy(self, enemy_id: str, size: int = 28) -> pygame.Surface:
        key = (enemy_id, size)
        if key not in self._enemies:
            self._enemies[key] = make_enemy_sprite(enemy_id, size)
        return self._enemies[key]

    def hero(self, size: int = 24) -> pygame.Surface:
        if size not in self._hero:
            self._hero[size] = make_hero_sprite(size)
        return self._hero[size]
