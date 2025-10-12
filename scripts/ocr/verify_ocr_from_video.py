import cv2
import os
import json
import shutil
import hashlib
from glob import glob

INPUT_DIR = r'C:\pokemon-ai-tool\.traindata\video\input_videos'
OUTPUT_DIR = r'C:\pokemon-ai-tool\.traindata\text2img'
PROCESSED_DIR = r'C:\pokemon-ai-tool\.traindata\video\processed_videos'
ROI_FILE = r'C:\pokemon-ai-tool\instance\roi_config.json'
EXTRACT_PER_SECOND = 1  # 1秒に3枚抽出

# 読み取るROIをここで指定（空の場合は全ROIを処理）
TARGET_ROIS = ['terastal']  # 例: terastalとyour_ailmentのみ処理

def win_safe_path(path):
    if os.name == 'nt':
        return "\\\\?\\" + os.path.abspath(path)
    return path

with open(ROI_FILE, "r", encoding="utf-8") as f:
    roi_dict = json.load(f)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def process_video(video_path):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    print(f"\n▶ 動画処理開始: {video_name}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ 動画を開けませんでした: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_interval = max(int(fps / EXTRACT_PER_SECOND), 1)

    print(f"  - 解像度: {width}x{height}, FPS: {fps:.2f}, 間隔: {frame_interval}フレーム")

    frame_idx = 0
    save_count = 0
    short_hash = hashlib.md5(video_name.encode()).hexdigest()[:8]

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            # 各ROIに対して処理
            for roi_name, value in roi_dict.items():
                # 'reference_resolution' は座標データではないためスキップ
                if roi_name == 'reference_resolution':
                    continue
                
                # your_party と your_poke1～6 をスキップ
                if roi_name == 'your_party' or any(roi_name.startswith(f"your_poke{i}") for i in range(1, 7)):
                    continue
                
                # TARGET_ROISが指定されている場合は対象ROIのみ処理
                if TARGET_ROIS and roi_name not in TARGET_ROIS:
                    continue
                
                # 値が4つの要素を持つリストであることを確認
                if not (isinstance(value, list) and len(value) == 4):
                    print(f"警告: ROI '{roi_name}' の形式が不正です。スキップします。")
                    continue

                x, y, w, h = value
                if x + w > width or y + h > height:
                    continue

                roi_img = frame[y:y+h, x:x+w]
                if roi_img.size == 0:
                    continue

                roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
                os.makedirs(roi_dir, exist_ok=True)
                filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
                save_path = win_safe_path(os.path.join(roi_dir, filename))

                if not cv2.imwrite(save_path, roi_img):
                    print(f"⚠ 保存失敗: {save_path}")
                else:
                    save_count += 1

        frame_idx += 1

    cap.release()
    print(f"✅ {video_name} 処理完了（保存画像数: {save_count}）")
    shutil.move(video_path, os.path.join(PROCESSED_DIR, os.path.basename(video_path)))

def main():
    # TARGET_ROISの設定を表示
    if TARGET_ROIS:
        print(f"🎯 対象ROI: {TARGET_ROIS}")
    else:
        print("🎯 対象ROI: 全てのROI")
    
    while True:
        video_files = glob(os.path.join(INPUT_DIR, "*.mp4"))
        if not video_files:
            print("\n🎉 全ての動画処理が完了しました。")
            break

        for video_file in video_files:
            process_video(video_file)

if __name__ == "__main__":
    main()