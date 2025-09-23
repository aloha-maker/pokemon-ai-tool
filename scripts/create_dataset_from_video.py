
import cv2
import json
import os
import sys
import numpy as np

def get_scaled_rois(roi_config, video_width, video_height):
    """
    動画の解像度に合わせてROI座標をスケーリングする。
    """
    ref_width = 1920
    ref_height = 1080
    
    width_scale = video_width / ref_width
    height_scale = video_height / ref_height
    
    scaled_rois = {}
    for key, (x, y, w, h) in roi_config.items():
        if key == "reference_resolution":
            continue
        scaled_rois[key] = [
            int(x * width_scale),
            int(y * height_scale),
            int(w * width_scale),
            int(h * height_scale)
        ]
    return scaled_rois

def are_images_different(img1, img2, threshold=1000):
    """
    2つの画像が十分に異なるかどうかを判定する。
    """
    if img1 is None or img2 is None:
        return True
    # グレースケールに変換して差分を計算
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    return np.sum(diff) > threshold

def main(video_path, roi_json_path, output_dir, file_prefix):
    """
    動画からROIを切り出し、データセット用の画像とテキストファイルを生成する。
    """
    # --- パスの存在チェック ---
    if not os.path.exists(video_path):
        print(f"エラー: 動画ファイルが見つかりません: {video_path}")
        return
    if not os.path.exists(roi_json_path):
        print(f"エラー: ROI設定ファイルが見つかりません: {roi_json_path}")
        return
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"出力ディレクトリを作成しました: {output_dir}")

    # --- 設定と動画の読み込み ---
    with open(roi_json_path, 'r') as f:
        roi_config = json.load(f)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"エラー: 動画ファイルを開けません: {video_path}")
        return

    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    rois = get_scaled_rois(roi_config, video_width, video_height)
    target_rois = {
        "my_pokemon_name": rois["my_pokemon_name"],
        "opponent_pokemon_name": rois["opponent_pokemon_name"]
    }

    print("データセットの生成を開始します...")
    
    frame_interval = 30  # 30フレームごとに処理 (約1秒ごと)
    frame_count = 0
    saved_count = 0
    last_images = {"my_pokemon_name": None, "opponent_pokemon_name": None}

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            for name, (x, y, w, h) in target_rois.items():
                cropped_img = frame[y:y+h, x:x+w]
                
                # 前のフレームの画像と十分に異なる場合のみ保存
                if are_images_different(cropped_img, last_images[name]):
                    # ファイル名とパス
                    img_filename = f"{file_prefix}.exp.{saved_count}.png"
                    txt_filename = f"{file_prefix}.exp.{saved_count}.gt.txt"
                    img_path = os.path.join(output_dir, img_filename)
                    txt_path = os.path.join(output_dir, txt_filename)
                    
                    # 保存
                    cv2.imwrite(img_path, cropped_img)
                    
                    # 空のテキストファイルを作成
                    with open(txt_path, 'w') as f:
                        pass
                    
                    print(f"  -> 保存しました: {img_filename}")
                    
                    last_images[name] = cropped_img.copy()
                    saved_count += 1

        frame_count += 1

    cap.release()
    print(f"\n処理が完了しました。合計 {saved_count} 個の画像を生成しました。")
    print(f"出力先: {output_dir}")
    print("次に、各 `.gt.txt` ファイルに、対応する画像に表示されているポケモン名を手動で入力してください。")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("使用法: python create_dataset_from_video.py <video_path> <roi_json_path> <output_dir> <file_prefix>")
        print("  <video_path>:    処理対象の動画ファイルのパス")
        print("  <roi_json_path>: ROI設定JSONファイルのパス")
        print("  <output_dir>:    生成したデータセットを保存するディレクトリ")
        print("  <file_prefix>:   出力ファイル名のプレフィックス (例: jpn.pkmn)")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
