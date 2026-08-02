"""Export procedural sprites as 64x64 PNGs for any content IDs missing assets."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from game.content.loader import ContentRegistry
from game.ui.sprites import ASSETS_DIR, make_enemy_sprite, make_tile_sprite


def main() -> None:
    pygame.init()
    try:
        pygame.display.set_mode((1, 1))
    except pygame.error:
        pass

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    content = ContentRegistry()
    written: list[str] = []
    for card_id in content.cards:
        path = ASSETS_DIR / f"{card_id}.png"
        if path.exists():
            continue
        pygame.image.save(make_tile_sprite(card_id, 64), str(path))
        written.append(card_id)
    for enemy_id in content.enemies:
        path = ASSETS_DIR / f"{enemy_id}.png"
        if path.exists():
            continue
        pygame.image.save(make_enemy_sprite(enemy_id, 64), str(path))
        written.append(enemy_id)
    print(f"Wrote {len(written)} sprites: {', '.join(written) or '(none)'}")


if __name__ == "__main__":
    main()
