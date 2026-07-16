"""Player settings and tutorial progress."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Settings:
    sound_enabled: bool = True
    fullscreen: bool = False
    tutorial_done: bool = False

    def to_dict(self) -> dict:
        return {
            "sound_enabled": self.sound_enabled,
            "fullscreen": self.fullscreen,
            "tutorial_done": self.tutorial_done,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> Settings:
        data = data or {}
        return cls(
            sound_enabled=bool(data.get("sound_enabled", True)),
            fullscreen=bool(data.get("fullscreen", False)),
            tutorial_done=bool(data.get("tutorial_done", False)),
        )


TUTORIAL_STEPS: list[dict[str, str]] = [
    {
        "title": "歡迎來到虛空邊境",
        "body": "你不直接操控英雄。英雄會自動繞圈戰鬥，你負責放牌與裝備。",
    },
    {
        "title": "規劃模式",
        "body": "現在是規劃模式（時間暫停）。從左側手牌選一張卡，地圖上高亮的格子可以放置。",
    },
    {
        "title": "放置卡牌",
        "body": "道路卡放在圓形道路上，地貌卡放在外圍格子。放牌會增加 Boss 計量。",
    },
    {
        "title": "開始冒險",
        "body": "點「繼續」或按空白鍵進入冒險模式，英雄會開始行走與戰鬥。",
    },
    {
        "title": "撤退與資源",
        "body": "在營火格撤退可保留 100% 資源；途中 60%；死亡 30%。資源用來建設營地。",
    },
    {
        "title": "準備好了",
        "body": "先放幾張草地／岩石撐住生命，再放敵人卡。祝你好運！",
    },
]
