# Video to Sprite Sheet Converter

將影片轉換成 Sprite Sheet 圖集的命令列工具。

## 功能特點

- 🎬 支援多種影片格式（MP4, AVI, MOV, MKV 等）
- 🖼️ 自動將影片幀合成為單一 Sprite Sheet 圖片
- 📐 可自訂幀尺寸、排列方式
- ⏱️ 支援擷取特定時間範圍
- 📄 可選輸出 JSON metadata（記錄每幀位置資訊）

## 系統需求

- Python 3.7+
- [FFmpeg](https://ffmpeg.org/download.html)（需安裝並加入系統 PATH）

## 安裝

1. 安裝 FFmpeg：
   - **Windows**: 從 [FFmpeg 官網](https://ffmpeg.org/download.html) 下載，解壓後將 `bin` 目錄加入系統 PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

2. 安裝 Python 依賴：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 基本使用

```bash
python video_to_spritesheet.py input.mp4
```

這會以預設設定（每秒 10 幀）將影片轉換為 `spritesheet.png`。

### 完整參數

```bash
python video_to_spritesheet.py input.mp4 [選項]
```

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `-o`, `--output` | 輸出檔案名稱 | `spritesheet.png` |
| `-f`, `--fps` | 抽取幀率 | `10` |
| `-w`, `--width` | 每幀寬度（像素） | 保持原始 |
| `-H`, `--height` | 每幀高度（像素） | 保持原始 |
| `-c`, `--columns` | 每行幾個幀 | 自動計算 |
| `--start` | 起始時間（秒） | 從頭開始 |
| `--end` | 結束時間（秒） | 到結尾 |
| `--max-frames` | 最大幀數限制 | 無限制 |
| `--json` | 輸出 JSON metadata | 否 |

### 使用範例

```bash
# 基本轉換
python video_to_spritesheet.py myvideo.mp4

# 自訂輸出檔名和幀率
python video_to_spritesheet.py myvideo.mp4 -o output.png -f 15

# 設定每幀尺寸為 128x128
python video_to_spritesheet.py myvideo.mp4 -w 128 -H 128

# 設定每行 10 個幀
python video_to_spritesheet.py myvideo.mp4 -c 10

# 只擷取前 5 秒
python video_to_spritesheet.py myvideo.mp4 --start 0 --end 5

# 擷取第 10 秒到第 20 秒
python video_to_spritesheet.py myvideo.mp4 --start 10 --end 20

# 限制最多 100 幀
python video_to_spritesheet.py myvideo.mp4 --max-frames 100

# 輸出 JSON metadata
python video_to_spritesheet.py myvideo.mp4 --json

# 組合使用
python video_to_spritesheet.py myvideo.mp4 -o sprite.png -f 12 -w 64 -H 64 -c 8 --json
```

## 輸出說明

### Sprite Sheet 圖片

輸出的 PNG 圖片會將所有幀按照行列排列：

```
┌───┬───┬───┬───┐
│ 0 │ 1 │ 2 │ 3 │
├───┼───┼───┼───┤
│ 4 │ 5 │ 6 │ 7 │
├───┼───┼───┼───┤
│ 8 │ 9 │...│...│
└───┴───┴───┴───┘
```

### JSON Metadata

使用 `--json` 參數時，會產生對應的 `.json` 檔案：

```json
{
  "frames": [
    {"index": 0, "x": 0, "y": 0, "w": 128, "h": 128},
    {"index": 1, "x": 128, "y": 0, "w": 128, "h": 128},
    ...
  ],
  "meta": {
    "size": {"w": 512, "h": 512},
    "frameSize": {"w": 128, "h": 128},
    "columns": 4,
    "rows": 4,
    "totalFrames": 16
  }
}
```

## 常見問題

### Q: 出現「找不到 FFmpeg」錯誤？

請確認已安裝 FFmpeg 並將其加入系統 PATH。可在終端機執行 `ffmpeg -version` 確認是否安裝成功。

### Q: 輸出圖片太大怎麼辦？

- 使用 `-w` 和 `-H` 參數縮小每幀尺寸
- 使用 `-f` 參數降低幀率
- 使用 `--max-frames` 參數限制幀數
- 使用 `--start` 和 `--end` 參數只擷取需要的片段

### Q: 如何在遊戲引擎中使用？

大多數遊戲引擎（Unity、Godot、Phaser 等）都支援 Sprite Sheet。配合 `--json` 輸出的 metadata，可以方便地匯入並使用。

## 授權

MIT License
