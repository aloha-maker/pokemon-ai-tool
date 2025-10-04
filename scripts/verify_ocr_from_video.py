import cv2
import os
import json
import shutil
import hashlib
from glob import glob

# === 設定 ===
INPUT_DIR = r'C:\Users\daiki\Videos\pokemon\input_videos'
OUTPUT_DIR = r'C:\Users\daiki\Videos\pokemon\cropped_images'
PROCESSED_DIR = r'C:\Users\daiki\Videos\pokemon\processed_videos'
ROI_FILE = r'C:\pokemon-ai-tool\roi_config.json'
EXTRACT_PER_SECOND = 0.3  # 1秒に3枚抽出

# Windows 長パス対応
def win_safe_path(path):
    if os.name == 'nt':
        return "\\\\?\\" + os.path.abspath(path)
    return path

# ROI 読み込み
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
            for roi_name, (x, y, w, h) in roi_dict.items():
                if x + w > width or y + h > height:
                    continue

                roi_img = frame[y:y+h, x:x+w]
                if roi_img.size == 0:
                    continue

                # 保存ディレクトリ作成
                roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
                os.makedirs(roi_dir, exist_ok=True)

                # 短いファイル名
                base_name = f"{short_hash}_{frame_idx:06d}"
                img_path = win_safe_path(os.path.join(roi_dir, base_name + ".jpg"))
                txt_path = win_safe_path(os.path.join(roi_dir, base_name + ".txt"))

                # 画像保存
                if cv2.imwrite(img_path, roi_img):
                    # OCR学習用テキストファイル作成
                    with open(txt_path, "w", encoding="utf-8") as t:
                        t.write(roi_name)  # ROI名をそのままラベルとして保存
                    save_count += 1
                else:
                    print(f"⚠ 保存失敗: {img_path}")

        frame_idx += 1

    cap.release()
    print(f"✅ {video_name} 処理完了（保存画像数: {save_count}）")

    # 処理済フォルダへ移動
    shutil.move(video_path, os.path.join(PROCESSED_DIR, os.path.basename(video_path)))

def main():
    while True:
        video_files = glob(os.path.join(INPUT_DIR, "*.mp4"))
        if not video_files:
            print("\n🎉 全ての動画処理が完了しました。")
            break

        for video_file in video_files:
            process_video(video_file)

if __name__ == "__main__":
    main()
