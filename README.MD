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
PYTHONPATH=. python scripts/playtest.py
```

## 操作

- **主選單**：開始遠征 / 營地建設 / 設定 / 清除存檔
- **教學**：首次遠征會引導；設定可重播
- **遠征**：左側選手牌 → 合法格會高亮 → 點擊地圖放置
- **裝備**：規劃模式下懸停背包可看屬性對比，點擊裝備
- **快捷鍵**：空白鍵 暫停/繼續、R 撤退、Esc 取消選牌、Del 清檔
- **設定**：音效開關、全螢幕、重播教學（寫入 `save/camp.json`）
- **營地**：點擊建築建造（解鎖新卡牌），進度自動存檔

## 美術與音效

- 像素 sprite：程序化產生（`game/ui/sprites.py`）
- 音效：合成 SFX（可在設定關閉）
