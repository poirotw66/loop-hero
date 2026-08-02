"""Card and enemy color mapping for procedural icons."""

from __future__ import annotations

CARD_COLORS: dict[str, tuple[int, int, int]] = {
    "camp": (200, 120, 60),
    "wasteland": (70, 65, 55),
    "cemetery": (100, 100, 110),
    "grove": (40, 100, 50),
    "swamp": (50, 80, 60),
    "village": (180, 160, 80),
    "spider_cocoon": (120, 80, 140),
    "vampire_mansion": (120, 40, 60),
    "battlefield": (140, 90, 70),
    "road_lantern": (220, 200, 100),
    "goblin_camp": (80, 130, 50),
    "rock": (110, 105, 100),
    "mountain": (90, 95, 110),
    "meadow": (70, 150, 70),
    "blooming_meadow": (100, 190, 90),
    "forest": (30, 90, 40),
    "treasury": (200, 170, 50),
    "empty_treasury": (150, 130, 40),
    "mountain_peak": (180, 180, 200),
    "bandit_camp": (130, 70, 50),
    "oblivion": (40, 20, 55),
    "ruins": (120, 95, 70),
    "thicket": (25, 70, 35),
    "desert": (190, 160, 90),
    "beacon": (230, 200, 120),
    "chrono_crystal": (80, 180, 210),
    "watch_post": (150, 120, 70),
}

ENEMY_COLORS: dict[str, tuple[int, int, int]] = {
    "slime": (80, 200, 80),
    "wolf": (140, 120, 100),
    "skeleton": (200, 200, 190),
    "spider": (60, 50, 70),
    "vampire": (160, 40, 50),
    "goblin": (90, 140, 60),
    "mosquito": (100, 100, 130),
    "gargoyle": (100, 100, 110),
    "harpy": (150, 130, 180),
    "bandit": (130, 90, 60),
    "mimic": (160, 120, 50),
    "void_warden": (80, 60, 160),
    "scorch_worm": (200, 110, 50),
    "memory_rift": (120, 70, 180),
}

RARITY_COLORS: dict[str, tuple[int, int, int]] = {
    "common": (160, 160, 170),
    "rare": (80, 140, 220),
    "epic": (200, 160, 60),
}

SLOT_LABELS: dict[str, str] = {
    "weapon": "武器",
    "armor": "盔甲",
    "shield": "盾牌",
    "ring": "戒指",
}
