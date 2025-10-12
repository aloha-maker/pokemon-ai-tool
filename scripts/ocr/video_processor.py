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


class PhaseManager:
    """フェーズ管理クラス"""
    def __init__(self):
        self.current_phase = "stay"  # stay, select, battle
        self.battle_sub_phase = "choose"  # choose, act
        self.processed_flags = {
            'stay_text': False,
            'select': False,
            'opponent_name': False,
            'start': False,
            'my_pokemon_name': False,
            'my_pokemon_hp': False,
            'my_ailment': False,
            'opponent_pokemon_name': False,
            'opponent_pokemon_hp': False,
            'your_ailment': False
        }
    
    def reset_battle_flags(self):
        """バトルフェーズのフラグをリセット"""
        self.processed_flags['my_pokemon_name'] = False
        self.processed_flags['my_pokemon_hp'] = False
        self.processed_flags['my_ailment'] = False
        self.processed_flags['opponent_pokemon_name'] = False
        self.processed_flags['opponent_pokemon_hp'] = False
        self.processed_flags['your_ailment'] = False
    
    def should_process_roi(self, roi_name):
        """ROIを処理すべきか判定"""
        if roi_name in self.processed_flags:
            return not self.processed_flags[roi_name]
        return True
    
    def mark_processed(self, roi_name):
        """ROI処理済みマーク"""
        if roi_name in self.processed_flags:
            self.processed_flags[roi_name] = True


def process_video(video_path, pokemon_corrector, ability_corrector, ocr_processor):
    """
    1本の動画をフレーム単位で処理し、OCR結果やROI画像を保存する
    """
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    print(f"\n▶ 動画処理開始: {video_name}")

    # フェーズ管理の初期化
    phase_manager = PhaseManager()

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
            print(f"  📊 フレーム {frame_idx}: フェーズ={phase_manager.current_phase}.{phase_manager.battle_sub_phase}")

            # フェーズ判定を実行
            phase_manager = ocr_processor.detect_phase(frame, phase_manager, width, height)

            # フェーズに応じたROI処理
            processed_count = ocr_processor.process_phase_rois(
                frame, phase_manager, video_name, frame_idx, short_hash, width, height
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