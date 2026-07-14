# Loop Hero-like Game

建立 Loop Hero 類似的自動 loop 策略遊戲。

## 文件

- [MVP 遊戲內容設計規格](docs/superpowers/specs/2026-07-11-loop-hero-mvp-game-content-design.md)

## 執行

```bash
pip install -r requirements.txt
python main.py
```

## 測試

```bash
PYTHONPATH=. pytest tests/ -v
```

## 操作

- **主選單**：開始遠征 / 營地建設
- **遠征**：左側選手牌 → 點擊地圖放置 →「暫停/繼續」切換模式 →「撤退」結束
- **裝備**：規劃模式下點擊右側背包物品裝備（自動替換同槽位）
- **快捷鍵**：空白鍵 暫停/繼續、R 撤退、Esc 取消選牌
- **營地**：點擊建築建造（解鎖新卡牌）