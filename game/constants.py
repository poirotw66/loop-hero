"""Global tuning constants for MVP."""

# Boss appears after ~8 placed cards (was 13 — unreachable with starter hand).
BOSS_METER_MAX = 64
BOSS_METER_PER_CARD = 8
DAY_DURATION_TICKS = 100
XP_PER_LEVEL = 80
ENEMY_HP_SCALE_PER_LOOP = 1.015
INVENTORY_MAX = 12
MAP_SIZE = 7
LOOP_LENGTH = 8
CAMP_LOOP_INDEX = 0

RETREAT_RATE_DEATH = 0.30
RETREAT_RATE_NORMAL = 0.60
RETREAT_RATE_CAMP = 1.00

RESOURCE_CHAIN = ["bone_dust", "hide", "herb", "metal"]
RESOURCE_STACK_SIZE = 10

# Closed clockwise loop (upper-left), leaving a 3x3 landscape zone for mountain peak.
# Index 0 is camp. Must match UI road rendering.
ROAD_COORDS: list[tuple[int, int]] = [
    (1, 1),
    (1, 2),
    (1, 3),
    (2, 3),
    (3, 3),
    (3, 2),
    (3, 1),
    (2, 1),
]
