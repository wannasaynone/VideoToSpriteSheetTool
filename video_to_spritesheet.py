#!/usr/bin/env python3
"""
Video to Sprite Sheet Converter
將影片轉換成 Sprite Sheet 圖集的命令列工具

使用方法:
    python video_to_spritesheet.py input.mp4 -o output.png [選項]
"""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("錯誤: 請先安裝 Pillow 套件")
    print("執行: pip install Pillow")
    sys.exit(1)

# rembg 是可選的依賴
REMBG_AVAILABLE = False
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    pass


def check_ffmpeg():
    """檢查 FFmpeg 是否已安裝"""
    if shutil.which("ffmpeg") is None:
        print("錯誤: 找不到 FFmpeg")
        print("請先安裝 FFmpeg 並確保它在系統 PATH 中")
        print("下載: https://ffmpeg.org/download.html")
        sys.exit(1)


def get_video_info(video_path):
    """取得影片資訊"""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(video_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        
        # 找到影片串流
        video_stream = None
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break
        
        if video_stream is None:
            print("錯誤: 找不到影片串流")
            sys.exit(1)
        
        return {
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "duration": float(info.get("format", {}).get("duration", 0)),
            "fps": eval(video_stream.get("r_frame_rate", "30/1"))
        }
    except subprocess.CalledProcessError as e:
        print(f"錯誤: 無法讀取影片資訊 - {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("錯誤: 無法解析影片資訊")
        sys.exit(1)


def extract_frames(video_path, output_dir, fps, start_time=None, end_time=None, max_frames=None):
    """從影片中抽取幀"""
    cmd = ["ffmpeg", "-y"]
    
    # 起始時間
    if start_time is not None:
        cmd.extend(["-ss", str(start_time)])
    
    cmd.extend(["-i", str(video_path)])
    
    # 結束時間
    if end_time is not None:
        if start_time is not None:
            duration = end_time - start_time
        else:
            duration = end_time
        cmd.extend(["-t", str(duration)])
    
    # 幀率過濾器
    vf_filters = [f"fps={fps}"]
    cmd.extend(["-vf", ",".join(vf_filters)])
    
    # 最大幀數
    if max_frames is not None:
        cmd.extend(["-frames:v", str(max_frames)])
    
    # 輸出格式
    output_pattern = os.path.join(output_dir, "frame_%05d.png")
    cmd.append(output_pattern)
    
    print(f"正在抽取幀... (fps={fps})")
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"錯誤: FFmpeg 執行失敗")
        print(e.stderr.decode() if e.stderr else "")
        sys.exit(1)
    
    # 取得所有抽取的幀
    frames = sorted(Path(output_dir).glob("frame_*.png"))
    print(f"已抽取 {len(frames)} 幀")
    
    return frames


def create_spritesheet(frames, output_path, frame_width=None, frame_height=None, columns=None, remove_bg=False):
    """將幀合成為 Sprite Sheet"""
    if not frames:
        print("錯誤: 沒有可用的幀")
        sys.exit(1)
    
    # 載入第一幀來取得尺寸
    first_frame = Image.open(frames[0])
    original_width, original_height = first_frame.size
    
    # 計算每幀的尺寸
    if frame_width and frame_height:
        target_width = frame_width
        target_height = frame_height
    elif frame_width:
        ratio = frame_width / original_width
        target_width = frame_width
        target_height = int(original_height * ratio)
    elif frame_height:
        ratio = frame_height / original_height
        target_width = int(original_width * ratio)
        target_height = frame_height
    else:
        target_width = original_width
        target_height = original_height
    
    # 計算行列數
    num_frames = len(frames)
    if columns:
        cols = columns
        rows = math.ceil(num_frames / cols)
    else:
        # 自動計算最佳排列（接近正方形）
        cols = math.ceil(math.sqrt(num_frames))
        rows = math.ceil(num_frames / cols)
    
    # 建立 Sprite Sheet
    sheet_width = cols * target_width
    sheet_height = rows * target_height
    
    print(f"Sprite Sheet 尺寸: {sheet_width} x {sheet_height}")
    print(f"排列: {cols} 列 x {rows} 行")
    print(f"每幀尺寸: {target_width} x {target_height}")
    if remove_bg:
        print("背景移除: 啟用")
    
    spritesheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # 記錄 metadata
    metadata = {
        "frames": [],
        "meta": {
            "size": {"w": sheet_width, "h": sheet_height},
            "frameSize": {"w": target_width, "h": target_height},
            "columns": cols,
            "rows": rows,
            "totalFrames": num_frames
        }
    }
    
    # 合成每一幀
    for i, frame_path in enumerate(frames):
        col = i % cols
        row = i // cols
        x = col * target_width
        y = row * target_height
        
        # 載入並縮放幀
        frame = Image.open(frame_path)
        if frame.size != (target_width, target_height):
            frame = frame.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 確保是 RGBA 模式
        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")
        
        # 移除背景
        if remove_bg:
            frame = rembg_remove(frame)
        
        # 貼上幀
        spritesheet.paste(frame, (x, y))
        
        # 記錄 metadata
        metadata["frames"].append({
            "index": i,
            "x": x,
            "y": y,
            "w": target_width,
            "h": target_height
        })
        
        # 顯示進度
        progress = (i + 1) / num_frames * 100
        print(f"\r合成進度: {progress:.1f}%", end="", flush=True)
    
    print()  # 換行
    
    # 儲存 Sprite Sheet
    spritesheet.save(output_path, "PNG")
    print(f"已儲存: {output_path}")
    
    return metadata


def save_metadata(metadata, output_path):
    """儲存 metadata 為 JSON 檔案"""
    json_path = Path(output_path).with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"已儲存 metadata: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="將影片轉換成 Sprite Sheet 圖集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  %(prog)s video.mp4
  %(prog)s video.mp4 -o spritesheet.png -f 15
  %(prog)s video.mp4 -w 128 -H 128 -c 10
  %(prog)s video.mp4 --start 0 --end 5 --json
  %(prog)s video.mp4 --remove-bg -o transparent.png
        """
    )
    
    parser.add_argument("input", help="輸入影片檔案路徑")
    parser.add_argument("-o", "--output", default="spritesheet.png", help="輸出檔案名稱 (預設: spritesheet.png)")
    parser.add_argument("-f", "--fps", type=float, default=10, help="抽取幀率 (預設: 10)")
    parser.add_argument("-w", "--width", type=int, help="每幀寬度 (預設: 保持原始)")
    parser.add_argument("-H", "--height", type=int, help="每幀高度 (預設: 保持原始)")
    parser.add_argument("-c", "--columns", type=int, help="每行幾個幀 (預設: 自動計算)")
    parser.add_argument("--start", type=float, help="起始時間 (秒)")
    parser.add_argument("--end", type=float, help="結束時間 (秒)")
    parser.add_argument("--max-frames", type=int, help="最大幀數限制")
    parser.add_argument("--json", action="store_true", help="輸出 JSON metadata")
    parser.add_argument("--remove-bg", action="store_true", help="移除背景 (需要安裝 rembg)")
    
    args = parser.parse_args()
    
    # 檢查輸入檔案
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"錯誤: 找不到輸入檔案 - {input_path}")
        sys.exit(1)
    
    # 檢查 FFmpeg
    check_ffmpeg()
    
    # 檢查 rembg
    if args.remove_bg and not REMBG_AVAILABLE:
        print("錯誤: 使用 --remove-bg 需要安裝 rembg")
        print("執行以下其中一個指令:")
        print('  pip install "rembg[cpu]"    # CPU 版本')
        print('  pip install "rembg[gpu]"    # GPU 版本 (需要 NVIDIA/CUDA)')
        sys.exit(1)
    
    # 取得影片資訊
    print(f"輸入影片: {input_path}")
    video_info = get_video_info(input_path)
    print(f"影片尺寸: {video_info['width']} x {video_info['height']}")
    print(f"影片長度: {video_info['duration']:.2f} 秒")
    print(f"影片 FPS: {video_info['fps']:.2f}")
    print()
    
    # 建立暫存目錄
    with tempfile.TemporaryDirectory() as temp_dir:
        # 抽取幀
        frames = extract_frames(
            input_path,
            temp_dir,
            fps=args.fps,
            start_time=args.start,
            end_time=args.end,
            max_frames=args.max_frames
        )
        
        if not frames:
            print("錯誤: 未能抽取任何幀")
            sys.exit(1)
        
        print()
        
        # 建立 Sprite Sheet
        metadata = create_spritesheet(
            frames,
            args.output,
            frame_width=args.width,
            frame_height=args.height,
            columns=args.columns,
            remove_bg=args.remove_bg
        )
        
        # 儲存 metadata
        if args.json:
            save_metadata(metadata, args.output)
    
    print()
    print("✅ 轉換完成！")


if __name__ == "__main__":
    main()
