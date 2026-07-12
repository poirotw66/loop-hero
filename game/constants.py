"""Global tuning constants for MVP."""

BOSS_METER_MAX = 100
BOSS_METER_PER_CARD = 8
DAY_DURATION_TICKS = 120
XP_PER_LEVEL = 100
ENEMY_HP_SCALE_PER_LOOP = 1.02
INVENTORY_MAX = 12
MAP_SIZE = 7
LOOP_LENGTH = 8
CAMP_LOOP_INDEX = 0

RETREAT_RATE_DEATH = 0.30
RETREAT_RATE_NORMAL = 0.60
RETREAT_RATE_CAMP = 1.00

RESOURCE_CHAIN = ["bone_dust", "hide", "herb", "metal"]
RESOURCE_STACK_SIZE = 10

# Road tile grid coordinates (row, col) for 7x7 map, clockwise from camp.
ROAD_COORDS: list[tuple[int, int]] = [
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (2, 5),
    (3, 5),
    (4, 5),
    (4, 4),
]
