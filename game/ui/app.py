"""Pygame UI for Loop Hero MVP."""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

from game.camp.meta import CampState
from game.content.loader import ContentRegistry
from game.core.game_state import GameState
from game.models import ExpeditionPhase, GameMode

# ponytail: single-file UI; split when a second screen justifies it
COLORS = {
    "bg": (18, 18, 28),
    "panel": (32, 32, 48),
    "road": (90, 78, 58),
    "camp": (200, 120, 60),
    "grid": (48, 48, 64),
    "hero": (80, 180, 255),
    "text": (230, 230, 240),
    "accent": (255, 200, 80),
    "danger": (220, 80, 80),
    "ok": (80, 200, 120),
}

CELL = 48
GRID_ORIGIN = (420, 80)
FONT_NAME = None


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 720))
        pygame.display.set_caption("Loop Hero MVP")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 18)
        self.font_lg = pygame.font.SysFont(FONT_NAME, 24)
        self.content = ContentRegistry()
        self.state = GameState(content=self.content, camp=CampState())
        self.screen_mode = "menu"
        self.selected_card: str | None = None
        self.selected_building: str | None = None
        self.result_text = ""

    def run(self) -> None:
        while True:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                self._handle_event(event)
            if self.screen_mode == "expedition" and self.state.mode == GameMode.ADVENTURE:
                if self.state.phase == ExpeditionPhase.TRAVELING:
                    self.state.tick(delta=dt * 30)
            self._draw()
            pygame.display.flip()

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        pos = event.pos
        if self.screen_mode == "menu":
            if 380 <= pos[0] <= 640 and 260 <= pos[1] <= 310:
                self.state.start_expedition()
                self.screen_mode = "expedition"
            elif 380 <= pos[0] <= 640 and 330 <= pos[1] <= 380:
                self.screen_mode = "camp"
            return

        if self.screen_mode == "camp":
            if 40 <= pos[0] <= 160 and 620 <= pos[1] <= 660:
                self.screen_mode = "menu"
                return
            for index, building_id in enumerate(self.content.buildings.keys()):
                y = 120 + index * 70
                if 40 <= pos[0] <= 420 and y <= pos[1] <= y + 50:
                    if self.state.build_camp(building_id):
                        self.result_text = f"建造 {self.content.buildings[building_id].name_zh} 成功"
                    else:
                        self.result_text = "無法建造"
            return

        if self.screen_mode == "expedition":
            if self.state.phase == ExpeditionPhase.LEVEL_UP:
                for index in range(len(self.state.pending_trait_choices)):
                    x = 300 + index * 200
                    if x <= pos[0] <= x + 180 and 500 <= pos[1] <= 560:
                        self.state.choose_trait(self.state.pending_trait_choices[index])
                return

            if 20 <= pos[0] <= 140 and 620 <= pos[1] <= 660:
                kept = self.state.end_expedition(at_camp=self.state.hero_loop_index == 0)
                self.result_text = f"撤退！骨粉 {kept.bone_dust} 獸皮 {kept.hide}"
                self.screen_mode = "menu"
                return
            if 160 <= pos[0] <= 280 and 620 <= pos[1] <= 660:
                self.state.toggle_mode()
                return

            for index, card_id in enumerate(self.state.hand):
                y = 120 + index * 34
                if 20 <= pos[0] <= 200 and y <= pos[1] <= y + 28:
                    self.selected_card = card_id

            if self.selected_card and self.state.mode == GameMode.PLANNING:
                for loop_index in range(1, 8):
                    x, y = self._road_screen_pos(loop_index)
                    rect = pygame.Rect(x - 20, y - 20, 40, 40)
                    if rect.collidepoint(pos):
                        if self.state.place_card_from_hand(self.selected_card, loop_index=loop_index):
                            self.selected_card = None
                        return
                for row in range(7):
                    for col in range(7):
                        x, y = self._grid_screen_pos(row, col)
                        rect = pygame.Rect(x, y, CELL - 2, CELL - 2)
                        if rect.collidepoint(pos):
                            if self.state.place_card_from_hand(self.selected_card, grid_pos=(row, col)):
                                self.selected_card = None
                            return

    def _road_screen_pos(self, loop_index: int) -> tuple[int, int]:
        x, y = GRID_ORIGIN
        ox, oy = 0, 0
        positions = [(1, 0), (2, 0), (3, 0), (4, 0), (4, 1), (4, 2), (4, 3), (3, 3)]
        if loop_index < len(positions):
            ox, oy = positions[loop_index]
        return (x + ox * CELL + CELL // 2, y + oy * CELL + CELL // 2)

    def _grid_screen_pos(self, row: int, col: int) -> tuple[int, int]:
        x, y = GRID_ORIGIN
        return (x + col * CELL, y + row * CELL)

    def _draw(self) -> None:
        self.screen.fill(COLORS["bg"])
        if self.screen_mode == "menu":
            self._draw_menu()
        elif self.screen_mode == "camp":
            self._draw_camp()
        else:
            self._draw_expedition()

    def _draw_menu(self) -> None:
        title = self.font_lg.render("虛空邊境 — Loop Hero MVP", True, COLORS["accent"])
        self.screen.blit(title, (300, 120))
        pygame.draw.rect(self.screen, COLORS["panel"], (380, 260, 260, 50))
        self.screen.blit(self.font.render("開始遠征", True, COLORS["text"]), (450, 275))
        pygame.draw.rect(self.screen, COLORS["panel"], (380, 330, 260, 50))
        self.screen.blit(self.font.render("營地建設", True, COLORS["text"]), (450, 345))
        if self.state.camp.boss_defeated:
            win = self.font.render("已擊敗虛空守衛！第二章即將到來…", True, COLORS["ok"])
            self.screen.blit(win, (280, 420))

    def _draw_camp(self) -> None:
        self.screen.blit(self.font_lg.render("營地", True, COLORS["accent"]), (40, 40))
        resources = self.state.camp.resources
        res_text = f"骨粉 {resources.bone_dust}  獸皮 {resources.hide}  草藥 {resources.herb}  金屬 {resources.metal}"
        self.screen.blit(self.font.render(res_text, True, COLORS["text"]), (40, 80))
        for index, (building_id, building) in enumerate(self.content.buildings.items()):
            y = 120 + index * 70
            built = building_id in self.state.camp.built_buildings
            color = COLORS["ok"] if built else COLORS["panel"]
            pygame.draw.rect(self.screen, color, (40, y, 380, 50))
            cost = ", ".join(f"{k}:{v}" for k, v in building.cost.items()) or "免費"
            label = f"{building.name_zh} {'(已建)' if built else cost}"
            self.screen.blit(self.font.render(label, True, COLORS["text"]), (50, y + 15))
        self.screen.blit(self.font.render(self.result_text, True, COLORS["accent"]), (40, 560))
        pygame.draw.rect(self.screen, COLORS["danger"], (40, 620, 120, 40))
        self.screen.blit(self.font.render("返回", True, COLORS["text"]), (70, 630))

    def _draw_expedition(self) -> None:
        stats = self.state.hero_stats
        header = (
            f"HP {stats.hp:.0f}/{stats.max_hp:.0f}  "
            f"Loop {self.state.loop_count}  Day {self.state.day_count}  "
            f"Boss {self.state.boss_meter:.0f}/{100}"
        )
        self.screen.blit(self.font.render(header, True, COLORS["text"]), (20, 20))
        mode = "Planning" if self.state.mode == GameMode.PLANNING else "Adventure"
        phase = self.state.phase.value
        self.screen.blit(self.font.render(f"模式: {mode}  階段: {phase}", True, COLORS["accent"]), (20, 45))

        pygame.draw.rect(self.screen, COLORS["panel"], (20, 100, 200, 500))
        self.screen.blit(self.font.render("手牌", True, COLORS["text"]), (30, 105))
        for index, card_id in enumerate(self.state.hand):
            card = self.content.cards[card_id]
            y = 120 + index * 34
            color = COLORS["accent"] if card_id == self.selected_card else COLORS["grid"]
            pygame.draw.rect(self.screen, color, (25, y, 190, 28))
            self.screen.blit(self.font.render(card.name_zh, True, COLORS["text"]), (30, y + 5))

        for row in range(7):
            for col in range(7):
                x, y = self._grid_screen_pos(row, col)
                pygame.draw.rect(self.screen, COLORS["grid"], (x, y, CELL - 2, CELL - 2))
                tile = self.state.map.grid.get((row, col))
                if tile:
                    name = self.content.cards[tile.card_id].name_zh[:2]
                    self.screen.blit(self.font.render(name, True, COLORS["ok"]), (x + 8, y + 14))

        for loop_index in range(8):
            x, y = self._road_screen_pos(loop_index)
            tile = self.state.map.road_tile_at(loop_index)
            color = COLORS["camp"] if loop_index == 0 else COLORS["road"]
            pygame.draw.circle(self.screen, color, (x, y), 18)
            if loop_index == self.state.hero_loop_index:
                pygame.draw.circle(self.screen, COLORS["hero"], (x, y), 8)
            name = self.content.cards.get(tile.card_id)
            label = name.name_zh[:2] if name else "?"
            self.screen.blit(self.font.render(label, True, COLORS["text"]), (x - 12, y - 28))

        res = self.state.run_resources
        loot = f"骨粉 {res.bone_dust}  獸皮 {res.hide}  草藥 {res.herb}  金屬 {res.metal}"
        self.screen.blit(self.font.render(loot, True, COLORS["text"]), (420, 520))

        for line_index, line in enumerate(self.state.combat_log[-3:]):
            self.screen.blit(self.font.render(line, True, COLORS["danger"]), (420, 550 + line_index * 22))

        pygame.draw.rect(self.screen, COLORS["danger"], (20, 620, 120, 40))
        self.screen.blit(self.font.render("撤退", True, COLORS["text"]), (50, 630))
        pygame.draw.rect(self.screen, COLORS["panel"], (160, 620, 120, 40))
        toggle = "繼續" if self.state.mode == GameMode.PLANNING else "暫停"
        self.screen.blit(self.font.render(toggle, True, COLORS["text"]), (185, 630))

        if self.state.phase == ExpeditionPhase.LEVEL_UP:
            overlay = pygame.Surface((1024, 720), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(self.font_lg.render("選擇特質", True, COLORS["accent"]), (420, 440))
            for index, trait_id in enumerate(self.state.pending_trait_choices):
                trait = self.content.traits[trait_id]
                x = 300 + index * 200
                pygame.draw.rect(self.screen, COLORS["panel"], (x, 500, 180, 60))
                self.screen.blit(self.font.render(trait.name_zh, True, COLORS["text"]), (x + 10, 515))


def main() -> None:
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
