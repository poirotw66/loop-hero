"""Pygame UI for Loop Hero MVP."""

from __future__ import annotations

import sys

import pygame

from game.camp.save import DEFAULT_SAVE_PATH, delete_save, load_camp, save_camp
from game.constants import BOSS_METER_MAX
from game.content.loader import ContentRegistry
from game.core.game_state import GameState
from game.models import CardType, ExpeditionPhase, GameMode
from game.systems.placement import can_place_card
from game.ui.sfx import SoundBank
from game.ui.sprites import SpriteAtlas
from game.ui.theme import CARD_COLORS, RARITY_COLORS, SLOT_LABELS

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
    "dim": (140, 140, 160),
    "legal": (60, 180, 120),
    "compare_up": (90, 210, 130),
    "compare_down": (220, 110, 110),
}

CELL = 48
GRID_ORIGIN = (380, 80)
PANEL_LEFT = (20, 100, 210, 500)
PANEL_EQUIP = (860, 80, 150, 620)
INV_START_Y = 330
FONT_NAME = None


class GameApp:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 720))
        pygame.display.set_caption("Loop Hero MVP")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 18)
        self.font_sm = pygame.font.SysFont(FONT_NAME, 14)
        self.font_lg = pygame.font.SysFont(FONT_NAME, 24)
        self.content = ContentRegistry()
        self.state = GameState(content=self.content, camp=load_camp())
        self.sprites = SpriteAtlas()
        self.sfx = SoundBank()
        self.screen_mode = "menu"
        self.selected_card: str | None = None
        self.hovered_inventory: int | None = None
        self.result_text = ""
        self.combat_flash = 0.0
        self._boss_warned = False
        self.save_status = "已載入存檔" if DEFAULT_SAVE_PATH.exists() else "新進度"

    def _persist(self) -> None:
        save_camp(self.state.camp)
        self.save_status = "進度已儲存"

    def run(self) -> None:
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.combat_flash = max(0.0, self.combat_flash - dt)
            mouse = pygame.mouse.get_pos()
            self.hovered_inventory = self._inventory_index_at(mouse)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._persist()
                    pygame.quit()
                    sys.exit(0)
                if event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)

            if self.screen_mode == "expedition":
                if self.state.boss_pending and not self._boss_warned:
                    self.sfx.play("boss")
                    self._boss_warned = True
                if self.state.phase == ExpeditionPhase.ENDED:
                    if self.state.last_died:
                        self.sfx.play("death")
                    elif self.state.boss_defeated_this_run:
                        self.sfx.play("victory")
                    else:
                        self.sfx.play("retreat")
                    self._persist()
                    self.screen_mode = "result"
                elif self.state.mode == GameMode.ADVENTURE and self.state.phase == ExpeditionPhase.TRAVELING:
                    before_log = len(self.state.combat_log)
                    self.state.tick(delta=dt * 30)
                    if len(self.state.combat_log) > before_log:
                        self.combat_flash = 0.25
                        self.sfx.play("hit")
                elif self.state.phase == ExpeditionPhase.LEVEL_UP:
                    pass

            self._draw()
            pygame.display.flip()

    def _inventory_index_at(self, pos: tuple[int, int]) -> int | None:
        if self.screen_mode != "expedition":
            return None
        for index in range(len(self.state.inventory)):
            y = INV_START_Y + index * 36
            if 870 <= pos[0] <= 1010 and y <= pos[1] <= y + 32:
                return index
        return None

    def _handle_key(self, key: int) -> None:
        if self.screen_mode == "expedition":
            if key == pygame.K_SPACE:
                self.state.toggle_mode()
            elif key == pygame.K_r:
                self._retreat()
            elif key == pygame.K_ESCAPE:
                self.selected_card = None
        elif self.screen_mode == "menu" and key == pygame.K_DELETE:
            delete_save()
            self.state.camp = load_camp()
            self.save_status = "存檔已清除"

    def _handle_click(self, pos: tuple[int, int]) -> None:
        if self.screen_mode == "menu":
            self._click_menu(pos)
        elif self.screen_mode == "camp":
            self._click_camp(pos)
        elif self.screen_mode == "result":
            self._click_result(pos)
        elif self.screen_mode == "expedition":
            self._click_expedition(pos)

    def _click_menu(self, pos: tuple[int, int]) -> None:
        if 380 <= pos[0] <= 640 and 260 <= pos[1] <= 310:
            self.state.start_expedition()
            self.selected_card = None
            self._boss_warned = False
            self.sfx.play("click")
            self.screen_mode = "expedition"
        elif 380 <= pos[0] <= 640 and 330 <= pos[1] <= 380:
            self.sfx.play("click")
            self.screen_mode = "camp"
        elif 380 <= pos[0] <= 640 and 400 <= pos[1] <= 450:
            delete_save()
            self.state.camp = load_camp()
            self.save_status = "存檔已清除"
            self.sfx.play("click")

    def _click_camp(self, pos: tuple[int, int]) -> None:
        if 40 <= pos[0] <= 160 and 620 <= pos[1] <= 660:
            self.screen_mode = "menu"
            return
        for index, building_id in enumerate(self.content.buildings.keys()):
            y = 120 + index * 70
            if 40 <= pos[0] <= 540 and y <= pos[1] <= y + 50:
                if self.state.build_camp(building_id):
                    building = self.content.buildings[building_id]
                    self.result_text = f"建造 {building.name_zh} 成功"
                    if building.unlocks_card:
                        card = self.content.cards[building.unlocks_card]
                        self.result_text += f"，解鎖 {card.name_zh}"
                    self._persist()
                    self.sfx.play("build")
                else:
                    self.result_text = "資源不足或已建造"
                    self.sfx.play("click")

    def _click_result(self, pos: tuple[int, int]) -> None:
        if 380 <= pos[0] <= 640 and 520 <= pos[1] <= 570:
            self.screen_mode = "menu"

    def _click_expedition(self, pos: tuple[int, int]) -> None:
        if self.state.phase == ExpeditionPhase.LEVEL_UP:
            for index in range(len(self.state.pending_trait_choices)):
                x = 200 + index * 220
                if x <= pos[0] <= x + 200 and 500 <= pos[1] <= 580:
                    self.state.choose_trait(self.state.pending_trait_choices[index])
                    self.sfx.play("level_up")
            return

        if 20 <= pos[0] <= 140 and 620 <= pos[1] <= 660:
            self._retreat()
            return
        if 160 <= pos[0] <= 280 and 620 <= pos[1] <= 660:
            self.state.toggle_mode()
            return

        for index, card_id in enumerate(self.state.hand):
            y = 120 + index * 34
            if 20 <= pos[0] <= 200 and y <= pos[1] <= y + 28:
                self.selected_card = card_id if self.selected_card != card_id else None

        inv_index = self._inventory_index_at(pos)
        if inv_index is not None and self.state.mode == GameMode.PLANNING:
            self.state.equip_item(inv_index)
            self.sfx.play("equip")
            return

        if self.selected_card and self.state.mode == GameMode.PLANNING:
            for loop_index in range(1, 8):
                x, y = self._road_screen_pos(loop_index)
                if pygame.Rect(x - 20, y - 20, 40, 40).collidepoint(pos):
                    if self.state.place_card_from_hand(self.selected_card, loop_index=loop_index):
                        self.selected_card = None
                        self.sfx.play("place")
                    return
            for row in range(7):
                for col in range(7):
                    x, y = self._grid_screen_pos(row, col)
                    if pygame.Rect(x, y, CELL - 2, CELL - 2).collidepoint(pos):
                        if self.state.place_card_from_hand(self.selected_card, grid_pos=(row, col)):
                            self.selected_card = None
                            self.sfx.play("place")
                        return

    def _retreat(self) -> None:
        at_camp = self.state.hero_loop_index == 0
        self.state.end_expedition(at_camp=at_camp)
        if self.state.boss_defeated_this_run:
            self.sfx.play("victory")
        else:
            self.sfx.play("retreat")
        self._persist()
        self.screen_mode = "result"

    def _road_screen_pos(self, loop_index: int) -> tuple[int, int]:
        from game.constants import ROAD_COORDS

        x, y = GRID_ORIGIN
        row, col = ROAD_COORDS[loop_index]
        return (x + col * CELL + CELL // 2, y + row * CELL + CELL // 2)

    def _grid_screen_pos(self, row: int, col: int) -> tuple[int, int]:
        x, y = GRID_ORIGIN
        return (x + col * CELL, y + row * CELL)

    def _draw(self) -> None:
        self.screen.fill(COLORS["bg"])
        if self.screen_mode == "menu":
            self._draw_menu()
        elif self.screen_mode == "camp":
            self._draw_camp()
        elif self.screen_mode == "result":
            self._draw_result()
        else:
            self._draw_expedition()

    def _draw_menu(self) -> None:
        title = self.font_lg.render("虛空邊境 — Loop Hero MVP", True, COLORS["accent"])
        self.screen.blit(title, (280, 100))
        self._draw_button(380, 260, 260, 50, "開始遠征")
        self._draw_button(380, 330, 260, 50, "營地建設")
        self._draw_button(380, 400, 260, 50, "清除存檔")
        res = self.state.camp.resources
        res_line = f"營地資源：骨粉 {res.bone_dust}  獸皮 {res.hide}  草藥 {res.herb}  金屬 {res.metal}"
        self.screen.blit(self.font.render(res_line, True, COLORS["dim"]), (240, 180))
        built = len(self.state.camp.built_buildings)
        self.screen.blit(self.font_sm.render(f"建築 {built}/5  |  {self.save_status}", True, COLORS["ok"]), (360, 210))
        if self.state.camp.boss_defeated:
            win = self.font.render("★ 已擊敗虛空守衛 — 第二章裂隙已開啟…", True, COLORS["ok"])
            self.screen.blit(win, (250, 480))
        hint = self.font_sm.render("空白鍵：暫停/繼續  |  R：撤退  |  Del：清檔", True, COLORS["dim"])
        self.screen.blit(hint, (300, 660))

    def _draw_camp(self) -> None:
        self.screen.blit(self.font_lg.render("營地", True, COLORS["accent"]), (40, 40))
        resources = self.state.camp.resources
        res_text = f"骨粉 {resources.bone_dust}  獸皮 {resources.hide}  草藥 {resources.herb}  金屬 {resources.metal}"
        self.screen.blit(self.font.render(res_text, True, COLORS["text"]), (40, 80))
        for index, (building_id, building) in enumerate(self.content.buildings.items()):
            y = 120 + index * 70
            built = building_id in self.state.camp.built_buildings
            can = self.state.camp.can_build(self.content, building_id)
            if built:
                color = COLORS["ok"]
            elif can:
                color = COLORS["panel"]
            else:
                color = (40, 40, 50)
            pygame.draw.rect(self.screen, color, (40, y, 500, 50))
            cost = ", ".join(f"{self._resource_name(k)}×{v}" for k, v in building.cost.items()) or "免費"
            unlock = ""
            if building.unlocks_card and not built:
                unlock = f" → 解鎖{self.content.cards[building.unlocks_card].name_zh}"
            label = f"{building.name_zh}  [{cost}]{unlock}" + (" ✓" if built else "")
            self.screen.blit(self.font.render(label, True, COLORS["text"]), (50, y + 15))
        if self.result_text:
            self.screen.blit(self.font.render(self.result_text, True, COLORS["accent"]), (40, 560))
        self.screen.blit(self.font_sm.render(self.save_status, True, COLORS["ok"]), (180, 630))
        self._draw_button(40, 620, 120, 40, "返回")

    def _draw_result(self) -> None:
        kept = self.state.last_kept_resources
        rate = int(self.state.last_retreat_rate * 100)
        if self.state.boss_defeated_this_run:
            title = "虛空守衛已擊敗！"
            title_color = COLORS["ok"]
        elif self.state.last_died:
            title = "遠征失敗"
            title_color = COLORS["danger"]
        else:
            title = "安全撤退"
            title_color = COLORS["accent"]

        self.screen.blit(self.font_lg.render(title, True, title_color), (380, 120))

        if self.state.last_died:
            detail = "英雄陣亡 — 僅保留 30% 資源"
            detail_color = COLORS["danger"]
        elif self.state.hero_loop_index == 0 or rate >= 100:
            detail = "於營火撤退 — 保留 100% 資源"
            detail_color = COLORS["ok"]
        else:
            detail = "途中撤退 — 保留 60% 資源"
            detail_color = COLORS["accent"]
        self.screen.blit(self.font.render(detail, True, detail_color), (340, 170))

        self.screen.blit(self.font.render(f"本趟 Loop {self.state.loop_count}  |  Day {self.state.day_count}", True, COLORS["dim"]), (360, 210))
        self.screen.blit(self.font.render(f"資源保留率：{rate}%", True, COLORS["text"]), (420, 250))
        lines = [
            f"骨粉 +{kept.bone_dust}",
            f"獸皮 +{kept.hide}",
            f"草藥 +{kept.herb}",
            f"金屬 +{kept.metal}",
        ]
        for index, line in enumerate(lines):
            self.screen.blit(self.font.render(line, True, COLORS["ok"]), (440, 290 + index * 30))
        if self.state.boss_defeated_this_run:
            teaser = self.font.render("虛空裂開一條縫隙… 第二章「記憶深處」即將到來", True, COLORS["accent"])
            self.screen.blit(teaser, (250, 430))
        self.screen.blit(self.font_sm.render("進度已自動儲存", True, COLORS["ok"]), (420, 480))
        self._draw_button(380, 520, 260, 50, "返回主選單")

    def _draw_expedition(self) -> None:
        stats = self.state.hero_stats
        header = (
            f"HP {stats.hp:.0f}/{stats.max_hp:.0f}  DMG {stats.damage:.0f}  DEF {stats.defense:.0f}  "
            f"Loop {self.state.loop_count}  Day {self.state.day_count}"
        )
        self.screen.blit(self.font.render(header, True, COLORS["text"]), (20, 20))
        mode_zh = "規劃" if self.state.mode == GameMode.PLANNING else "冒險"
        self.screen.blit(self.font.render(f"模式：{mode_zh}", True, COLORS["accent"]), (20, 45))
        self._draw_boss_meter()
        if self.state.boss_defeated_this_run:
            self.screen.blit(self.font_sm.render("Boss 已擊敗 — 回營火撤退！", True, COLORS["ok"]), (20, 95))
        elif self.state.boss_pending:
            self.screen.blit(self.font_sm.render("Boss 計量已滿 — 下次回營火將迎戰！", True, COLORS["danger"]), (20, 95))

        self._draw_hand_panel()
        self._draw_map()
        self._draw_equipment_panel()
        self._draw_hud_bottom()

        if self.state.phase == ExpeditionPhase.COMBAT or self.combat_flash > 0:
            self._draw_combat_overlay()
        if self.state.phase == ExpeditionPhase.LEVEL_UP:
            self._draw_level_up_overlay()

    def _draw_boss_meter(self) -> None:
        x, y, w, h = 280, 48, 280, 16
        pygame.draw.rect(self.screen, COLORS["panel"], (x, y, w, h))
        fill = min(1.0, self.state.boss_meter / BOSS_METER_MAX)
        color = COLORS["danger"] if fill >= 1.0 else COLORS["accent"]
        pygame.draw.rect(self.screen, color, (x, y, int(w * fill), h))
        pygame.draw.rect(self.screen, COLORS["text"], (x, y, w, h), 1)
        label = f"Boss {self.state.boss_meter:.0f}/{BOSS_METER_MAX}"
        self.screen.blit(self.font_sm.render(label, True, COLORS["text"]), (x + w + 10, y - 1))

    def _draw_hand_panel(self) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], PANEL_LEFT)
        self.screen.blit(self.font.render("手牌", True, COLORS["text"]), (30, 105))
        if self.selected_card and self.state.mode == GameMode.PLANNING:
            tip = self.font_sm.render("高亮格可放置", True, COLORS["legal"])
            self.screen.blit(tip, (30, 85))
        if not self.state.hand:
            self.screen.blit(self.font_sm.render("(空)", True, COLORS["dim"]), (30, 130))
        for index, card_id in enumerate(self.state.hand):
            card = self.content.cards[card_id]
            y = 120 + index * 34
            selected = card_id == self.selected_card
            color = COLORS["accent"] if selected else COLORS["grid"]
            pygame.draw.rect(self.screen, color, (25, y, 190, 28))
            type_tag = {"road": "道", "roadside": "邊", "landscape": "貌", "special": "特"}.get(card.card_type.value, "?")
            self.screen.blit(self.sprites.tile(card_id, 20), (28, y + 4))
            self.screen.blit(self.font.render(f"{card.name_zh} [{type_tag}]", True, COLORS["text"]), (54, y + 5))

    def _draw_map(self) -> None:
        legal_roads: set[int] = set()
        legal_cells: set[tuple[int, int]] = set()
        if self.selected_card and self.state.mode == GameMode.PLANNING:
            card = self.content.cards.get(self.selected_card)
            if card and card.card_type == CardType.ROAD:
                for loop_index in range(1, 8):
                    if can_place_card(self.content, self.state.map, self.selected_card, loop_index=loop_index):
                        legal_roads.add(loop_index)
            elif card:
                for row in range(7):
                    for col in range(7):
                        if can_place_card(self.content, self.state.map, self.selected_card, grid_pos=(row, col)):
                            legal_cells.add((row, col))

        for row in range(7):
            for col in range(7):
                x, y = self._grid_screen_pos(row, col)
                pygame.draw.rect(self.screen, COLORS["grid"], (x, y, CELL - 2, CELL - 2))
                if (row, col) in legal_cells:
                    pygame.draw.rect(self.screen, COLORS["legal"], (x, y, CELL - 2, CELL - 2), 2)
                tile = self.state.map.grid.get((row, col))
                if tile:
                    self._draw_tile_icon(x + 4, y + 4, CELL - 10, tile.card_id)

        for loop_index in range(8):
            x, y = self._road_screen_pos(loop_index)
            tile = self.state.map.road_tile_at(loop_index)
            card_id = tile.card_id
            radius = 20 if loop_index == 0 else 16
            color = CARD_COLORS.get(card_id, COLORS["road"])
            pygame.draw.circle(self.screen, color, (x, y), radius)
            sprite = self.sprites.tile(card_id if card_id != "wasteland" else "wasteland", 28 if loop_index else 32)
            self.screen.blit(sprite, (x - sprite.get_width() // 2, y - sprite.get_height() // 2))
            if loop_index in legal_roads:
                pygame.draw.circle(self.screen, COLORS["legal"], (x, y), radius + 4, 3)
            pygame.draw.circle(self.screen, COLORS["text"], (x, y), radius, 1)
            if loop_index == self.state.hero_loop_index:
                hero = self.sprites.hero(18)
                self.screen.blit(hero, (x - 9, y - 9))
            if tile.spawned_enemies:
                enemy_id = tile.spawned_enemies[0]
                enemy = self.sprites.enemy(enemy_id, 16)
                self.screen.blit(enemy, (x + 6, y + 2))
                if len(tile.spawned_enemies) > 1:
                    self.screen.blit(
                        self.font_sm.render(f"x{len(tile.spawned_enemies)}", True, COLORS["danger"]),
                        (x + 10, y + 16),
                    )
            label = self.content.cards.get(card_id)
            text = "營" if card_id == "camp" else (label.name_zh[:2] if label else "?")
            self.screen.blit(self.font_sm.render(text, True, COLORS["text"]), (x - 10, y - radius - 16))

    def _draw_tile_icon(self, x: int, y: int, size: int, card_id: str) -> None:
        sprite = self.sprites.tile(card_id, size)
        self.screen.blit(sprite, (x, y))

    def _draw_equipment_panel(self) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], PANEL_EQUIP)
        self.screen.blit(self.font.render("裝備", True, COLORS["text"]), (870, 88))
        slot_y = 115
        for slot in ("weapon", "armor", "shield", "ring"):
            pygame.draw.rect(self.screen, COLORS["grid"], (870, slot_y, 130, 36))
            item = self.state.equipped.get(slot)
            label = SLOT_LABELS[slot]
            if item:
                eq = self.content.equipment[item.def_id]
                rarity = RARITY_COLORS.get(eq.rarity, COLORS["dim"])
                pygame.draw.rect(self.screen, rarity, (873, slot_y + 3, 8, 30))
                text = f"{label}: {eq.name_zh[:6]}"
            else:
                text = f"{label}: —"
            self.screen.blit(self.font_sm.render(text, True, COLORS["text"]), (886, slot_y + 10))
            slot_y += 42

        self.screen.blit(self.font.render("背包", True, COLORS["text"]), (870, 288))
        self.screen.blit(
            self.font_sm.render(f"{len(self.state.inventory)}/{self.state.inventory_max}", True, COLORS["dim"]),
            (920, 290),
        )
        if self.state.mode != GameMode.PLANNING:
            self.screen.blit(self.font_sm.render("(規劃模式可裝備)", True, COLORS["dim"]), (870, 310))

        for index, item in enumerate(self.state.inventory):
            y = INV_START_Y + index * 36
            eq = self.content.equipment[item.def_id]
            rarity = RARITY_COLORS.get(eq.rarity, COLORS["dim"])
            bg = COLORS["accent"] if index == self.hovered_inventory else COLORS["grid"]
            pygame.draw.rect(self.screen, bg, (870, y, 130, 32))
            pygame.draw.rect(self.screen, rarity, (873, y + 3, 6, 26))
            self.screen.blit(self.font_sm.render(eq.name_zh, True, COLORS["text"]), (884, y + 8))

        if self.hovered_inventory is not None and self.hovered_inventory < len(self.state.inventory):
            self._draw_equip_compare(self.hovered_inventory)

        if self.state.hero_traits:
            self.screen.blit(self.font.render("特質", True, COLORS["text"]), (870, 580))
            for index, trait_id in enumerate(self.state.hero_traits[:3]):
                trait = self.content.traits[trait_id]
                self.screen.blit(self.font_sm.render(f"• {trait.name_zh}", True, COLORS["accent"]), (870, 605 + index * 18))

    def _draw_equip_compare(self, inventory_index: int) -> None:
        item = self.state.inventory[inventory_index]
        new_eq = self.content.equipment[item.def_id]
        current = self.state.equipped.get(item.slot)
        current_eq = self.content.equipment[current.def_id] if current else None

        box = pygame.Rect(620, 300, 230, 160)
        pygame.draw.rect(self.screen, COLORS["panel"], box)
        pygame.draw.rect(self.screen, COLORS["accent"], box, 1)
        self.screen.blit(self.font.render(f"對比 · {SLOT_LABELS[item.slot]}", True, COLORS["accent"]), (630, 308))
        self.screen.blit(self.font_sm.render(f"新：{new_eq.name_zh}", True, COLORS["text"]), (630, 335))
        cur_name = current_eq.name_zh if current_eq else "（空）"
        self.screen.blit(self.font_sm.render(f"現：{cur_name}", True, COLORS["dim"]), (630, 355))

        keys = sorted(set(new_eq.bonuses) | set(current_eq.bonuses if current_eq else {}))
        line_y = 380
        for key in keys[:5]:
            new_val = new_eq.bonuses.get(key, 0.0)
            old_val = current_eq.bonuses.get(key, 0.0) if current_eq else 0.0
            delta = new_val - old_val
            if abs(delta) < 1e-6 and key not in new_eq.bonuses:
                continue
            color = COLORS["compare_up"] if delta > 0 else COLORS["compare_down"] if delta < 0 else COLORS["dim"]
            sign = "+" if delta > 0 else ""
            text = f"{key}: {new_val:g} ({sign}{delta:g})"
            self.screen.blit(self.font_sm.render(text, True, color), (630, line_y))
            line_y += 18

    def _draw_hud_bottom(self) -> None:
        res = self.state.run_resources
        loot = f"本趟：骨粉 {res.bone_dust}  獸皮 {res.hide}  草藥 {res.herb}  金屬 {res.metal}"
        self.screen.blit(self.font.render(loot, True, COLORS["text"]), (380, 620))
        rate_hint = "營火撤退 100%  |  途中 60%  |  死亡 30%"
        if self.state.hero_loop_index == 0:
            rate_hint = "目前在營火 — 撤退保留 100%"
        self.screen.blit(self.font_sm.render(rate_hint, True, COLORS["dim"]), (380, 645))
        for index, msg in enumerate(self.state.messages[-2:]):
            self.screen.blit(self.font_sm.render(msg, True, COLORS["ok"]), (380, 560 + index * 18))
        self._draw_button(20, 620, 120, 40, "撤退")
        toggle = "繼續" if self.state.mode == GameMode.PLANNING else "暫停"
        self._draw_button(160, 620, 120, 40, toggle)

    def _draw_combat_overlay(self) -> None:
        overlay = pygame.Surface((1024, 720), pygame.SRCALPHA)
        alpha = 140 if self.state.phase == ExpeditionPhase.COMBAT else int(self.combat_flash * 200)
        overlay.fill((80, 20, 20, min(alpha, 180)))
        self.screen.blit(overlay, (0, 0))
        self.screen.blit(self.font_lg.render("戰鬥中", True, COLORS["danger"]), (460, 280))
        self.screen.blit(self.sprites.hero(48), (380, 320))
        # Show last fought enemies from road tile near hero if any remain in log context.
        self.screen.blit(self.sprites.enemy("slime", 48), (560, 320))
        for index, line in enumerate(self.state.combat_log[-4:]):
            self.screen.blit(self.font.render(line, True, COLORS["text"]), (300, 390 + index * 26))

    def _draw_level_up_overlay(self) -> None:
        overlay = pygame.Surface((1024, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        self.screen.blit(self.font_lg.render(f"升級！Lv.{self.state.hero_level} — 選擇特質", True, COLORS["accent"]), (320, 440))
        for index, trait_id in enumerate(self.state.pending_trait_choices):
            trait = self.content.traits[trait_id]
            x = 200 + index * 220
            pygame.draw.rect(self.screen, COLORS["panel"], (x, 500, 200, 80))
            self.screen.blit(self.font.render(trait.name_zh, True, COLORS["accent"]), (x + 10, 510))
            desc = trait.description_zh
            if len(desc) > 18:
                self.screen.blit(self.font_sm.render(desc[:18], True, COLORS["text"]), (x + 10, 535))
                self.screen.blit(self.font_sm.render(desc[18:], True, COLORS["text"]), (x + 10, 552))
            else:
                self.screen.blit(self.font_sm.render(desc, True, COLORS["text"]), (x + 10, 540))

    def _draw_button(self, x: int, y: int, w: int, h: int, label: str) -> None:
        pygame.draw.rect(self.screen, COLORS["panel"], (x, y, w, h))
        pygame.draw.rect(self.screen, COLORS["accent"], (x, y, w, h), 1)
        text = self.font.render(label, True, COLORS["text"])
        self.screen.blit(text, (x + (w - text.get_width()) // 2, y + (h - text.get_height()) // 2))

    def _resource_name(self, resource_id: str) -> str:
        names = {"bone_dust": "骨粉", "hide": "獸皮", "herb": "草藥", "metal": "金屬"}
        return names.get(resource_id, resource_id)


def main() -> None:
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
