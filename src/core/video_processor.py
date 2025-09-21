import cv2
import os
import numpy as np
from src.core.ocr import GameStateParser
from src.database.manager import DatabaseManager
from src.core.turn_reconstructor import TurnReconstructor

class VideoProcessor:
    """
    動画ファイルを解析して、対戦ログを抽出するクラス。
    """
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.parser = GameStateParser()
        self.reconstructor = TurnReconstructor()
        self.templates = self._load_templates({
            "my_status": ".img/my_status.png"
        })

    def _load_templates(self, template_paths: dict) -> dict:
        loaded_templates = {}
        for name, path in template_paths.items():
            if not os.path.exists(path):
                print(f"警告: テンプレートファイルが見つかりません: {path}")
                continue
            template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                print(f"警告: テンプレートファイルの読み込みに失敗しました: {path}")
                continue
            loaded_templates[name] = template
            print(f"テンプレートを読み込みました: {path} (サイズ: {template.shape[1]}x{template.shape[0]})")
        return loaded_templates

    def analyze(self) -> dict:
        """
        動画を解析し、静止かつUIが表示された場面を検出してOCRを実行し、ターンごとの情報を抽出する。

        Returns:
            dict: 抽出したターンごとの情報のリストを含む辞書
        """
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {self.video_path}")

        extracted_states = []
        prev_frame_gray = None

        # --- 制御用の定数と変数 ---
        MOTION_THRESHOLD = 5000
        TEMPLATE_MATCH_THRESHOLD = 0.8
        ocr_triggered_on_static_frame = False

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Starting video analysis... Total frames: {total_frames}")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            current_frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # --- テンプレートマッチング --- 
            ui_found = False
            if self.templates:
                for name, template in self.templates.items():
                    res = cv2.matchTemplate(frame_gray, template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, _ = cv2.minMaxLoc(res)
                    if max_val >= TEMPLATE_MATCH_THRESHOLD:
                        ui_found = True
                        break

            # --- フレーム差分計算 ---
            blurred_gray = cv2.GaussianBlur(frame_gray, (5, 5), 0)
            motion_detected = False
            if prev_frame_gray is not None:
                frame_delta = cv2.absdiff(prev_frame_gray, blurred_gray)
                thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
                motion_amount = cv2.countNonZero(thresh)

                if motion_amount > MOTION_THRESHOLD:
                    motion_detected = True
                    if ocr_triggered_on_static_frame:
                        ocr_triggered_on_static_frame = False
            
            prev_frame_gray = blurred_gray

            # --- OCR実行判定 ---
            # UIが見つかり、静止していて、かつこの静止場面でまだOCRを実行していない場合
            if ui_found and not motion_detected and not ocr_triggered_on_static_frame:
                print(f"Static scene with UI found at frame {current_frame_num}. Running OCR...")
                state = self.parser.parse_frame(frame)
                
                if state and any(val for val in state.values() if val and not str(val).startswith("Error")):
                    print(f"  -> OCR successful. Extracted state: {state}")
                    extracted_states.append({"frame": current_frame_num, "state": state})
                else:
                    print("  -> No significant text found.")
                
                ocr_triggered_on_static_frame = True

        cap.release()
        print(f"Video analysis complete. Extracted states: {len(extracted_states)}")

        reconstructed_log = self.reconstructor.reconstruct(extracted_states)
        return reconstructed_log