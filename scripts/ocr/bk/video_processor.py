import os
import cv2
import hashlib
import shutil
from glob import glob

from config import (
    INPUT_DIR, OUTPUT_DIR, PROCESSED_DIR, ROI_DICT,
    POKEMON_NAME_ROIS, OTHER_ROIS, HP_ROIS, AILMENT_ROIS,
    SKIP_ROIS, OCR_EXEMPT_ROIS, EXTRACT_PER_SECOND
)
from utils import win_safe_path


def process_video(video_path, pokemon_corrector, ability_corrector, ocr_processor):
    """
    1本の動画をフレーム単位で処理し、OCR結果やROI画像を保存する
    """
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    print(f"\n▶ 動画処理開始: {video_name}")

    # 動画読み込み
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
    ocr_success_count = 0
    short_hash = hashlib.md5(video_name.encode()).hexdigest()[:8]

    # 名前履歴をリセット
    ocr_processor.last_my_pokemon_name = ""
    ocr_processor.last_opponent_pokemon_name = ""

    # 出力ディレクトリ作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # フレームループ
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 指定間隔でフレームを処理
        if frame_idx % frame_interval == 0:
            print(f"  📊 フレーム {frame_idx}: 処理開始")

            processed_pokemon = False
            pokemon_success = False

            # ==============================
            # ステップ1: ポケモン名ROIを優先処理
            # ==============================
            for roi_name in POKEMON_NAME_ROIS:
                if roi_name not in ROI_DICT or roi_name in SKIP_ROIS:
                    continue

                value = ROI_DICT[roi_name]
                if not (isinstance(value, list) and len(value) == 4):
                    continue

                success, max_conf = ocr_processor.process_roi_with_confidence_check(
                    frame, roi_name, value, width, height, video_name, frame_idx, short_hash
                )

                if success:
                    pokemon_success = True
                    save_count += 1
                    ocr_success_count += 1
                    processed_pokemon = True

            # ==============================
            # ステップ1a: 成功時は補助ROI（HP・状態異常）も保存
            # ==============================
            if pokemon_success:
                supplementary_count = ocr_processor.save_supplementary_roi_images(
                    frame, video_name, frame_idx, short_hash, width, height
                )
                save_count += supplementary_count
                print(f"  💚 ポケモン名ROI成功 → 補助ROI {supplementary_count}枚を保存")

            # ==============================
            # ステップ2: ポケモン名ROI失敗時、その他ROIを処理
            # ==============================
            if not pokemon_success:
                print(f"  🔄 ポケモン名ROI確信度不足 → 他ROI処理（補助ROI除外）")

                for roi_name in OTHER_ROIS:
                    if (
                        roi_name not in ROI_DICT or
                        roi_name in SKIP_ROIS or
                        roi_name in OCR_EXEMPT_ROIS
                    ):
                        continue

                    value = ROI_DICT[roi_name]
                    if not (isinstance(value, list) and len(value) == 4):
                        continue

                    success, max_conf = ocr_processor.process_roi_with_confidence_check(
                        frame, roi_name, value, width, height, video_name, frame_idx, short_hash
                    )

                    if success:
                        save_count += 1
                        ocr_success_count += 1
                        processed_pokemon = True

            # ==============================
            # ステップ3: 有効ROIがなかった場合
            # ==============================
            if not processed_pokemon:
                print(f"  ⏭️ フレーム {frame_idx}: 有効なROIなし（スキップ）")

        frame_idx += 1

    cap.release()

    # ==============================
    # 動画処理完了後
    # ==============================
    print(f"✅ {video_name} 処理完了（保存画像数: {save_count}, OCR成功: {ocr_success_count}）")

    # 処理済み動画を移動
    try:
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        dest_path = win_safe_path(os.path.join(PROCESSED_DIR, os.path.basename(video_path)))
        shutil.move(win_safe_path(video_path), dest_path)
        print(f"📦 動画を移動: {dest_path}")
    except Exception as e:
        print(f"⚠ 動画移動失敗: {e}")
