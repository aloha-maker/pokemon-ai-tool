# video_processor.py（更新版）
import os
import cv2
import hashlib
import shutil
from glob import glob

from config import (
    INPUT_DIR, OUTPUT_DIR, PROCESSED_DIR, ROI_DICT,
    POKEMON_NAME_ROIS, OTHER_ROIS, HP_ROIS, AILMENT_ROIS,
    SKIP_ROIS, OCR_EXEMPT_ROIS, EXTRACT_PER_SECOND,
    STAY_ROIS, SELECT_ROIS, BATTLE_CHOOSE_ROIS, BATTLE_ACT_ROIS,
    STAY_TEXT_IMAGE, START_IMAGE, SELECT_IMAGES_DIR, WIN_LOSE_IMAGES_DIR
)
from utils import win_safe_path
from phase_manager import PhaseManager


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

    # 新しい動画用に状態をリセット
    ocr_processor.reset_for_new_video()

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
            # 現在のフェーズ情報を取得（ログ表示用）
            current_phase_info = ocr_processor.get_current_phase_info()
            current_phase = current_phase_info['current_phase']
            battle_sub_phase = current_phase_info.get('battle_sub_phase', '')
            
            phase_display = current_phase
            if battle_sub_phase:
                phase_display += f".{battle_sub_phase}"
                
            print(f"  📊 フレーム {frame_idx}: フェーズ={phase_display}")

            # フェーズ判定を実行（act→choose遷移対応版）
            phase_manager = ocr_processor.detect_phase(frame, width, height)

            # フェーズに応じたROI処理
            processed_count = ocr_processor.process_phase_rois(
                frame, video_name, frame_idx, short_hash, width, height
            )
            
            save_count += processed_count
            if processed_count > 0:
                ocr_success_count += 1

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