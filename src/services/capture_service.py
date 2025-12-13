# src/services/capture_service.py
import os
import time
import cv2
import json
import numpy as np
from flask import current_app

class CaptureService:
    """
    画面キャプチャとOCR実行に関連するビジネスロジックを担当するサービスクラス
    """

    def __init__(self):
        self.debug_image_dir = '.img'
        self.roi_config_path = 'instance/roi_config.json'

    def recognize_opponent_party_from_frame(self) -> dict:
        """
        現在のフレーム画像から相手のパーティを認識する。

        Returns:
            dict: 認識結果。成功時は party と debug_info を、失敗時は error を含む。
        """
        frame = None
        # 1. メモリ上の最新フレームを試す (camera_capture_worker)
        with current_app.state.frame_lock:
            if current_app.state.latest_frame_bytes:
                np_arr = np.frombuffer(current_app.state.latest_frame_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # 3. どちらの方法でもフレームが取得できなかった場合
        if frame is None:
            return {
                "success": False,
                "error": "キャプチャ画像が見つかりません。リアルタイム解析が実行されているか確認してください。",
                "status_code": 404
            }

        # タイムスタンプで今回処理用のフォルダを作成
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_dir_for_this_run = os.path.join(self.debug_image_dir, timestamp)
        os.makedirs(output_dir_for_this_run, exist_ok=True)

        # 切り抜き前の全体画像を保存
        full_frame_save_path = os.path.join(output_dir_for_this_run, "full_frame.jpg")
        cv2.imwrite(full_frame_save_path, frame)

        try:
            with open(self.roi_config_path, 'r', encoding='utf-8') as f:
                roi_config = json.load(f)
        except FileNotFoundError:
            return {"success": False, "error": "ROI設定ファイルが見つかりません。", "status_code": 500}
        except json.JSONDecodeError:
            return {"success": False, "error": "ROI設定ファイルの解析に失敗しました。", "status_code": 500}

        party_rois = [roi_config.get(f'your_poke{i}') for i in range(1, 7)]
        roi_names = [f'your_poke{i}' for i in range(1, 7)]

        recognized_party = []
        debug_info = []

        for i, roi in enumerate(party_rois):
            roi_name = roi_names[i]
            pokemon_name = ""
            recognition_details = {}

            if roi and isinstance(roi, list) and len(roi) == 4:
                x, y, w, h = roi
                roi_image = frame[y:y+h, x:x+w]

                if roi_image.size > 0:
                    # 切り抜いたROI画像を保存
                    roi_filename = f"{roi_name}.png"
                    roi_save_path = os.path.join(output_dir_for_this_run, roi_filename)
                    cv2.imwrite(roi_save_path, roi_image)

                # `current_app`からrecognizerを取得して実行
                recognizer = current_app.pokemon_recognizer
                recognition_details = recognizer.recognize(roi_image)
                pokemon_name = recognition_details.get("name", "")
            
            recognized_party.append(pokemon_name)
            debug_info.append({
                "roi": roi_name,
                "recognized_name": pokemon_name,
                "best_match_template": recognition_details.get("template_name", ""),
                "score": round(recognition_details.get("score", 0.0), 4)
            })
        
        return {
            "success": True, 
            "party": recognized_party, 
            "debug_info": debug_info,
            "status_code": 200
        }
