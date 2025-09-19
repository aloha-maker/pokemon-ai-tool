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

    def analyze(self) -> dict:
        """
        動画を解析し、ターンごとの情報を抽出する。
        現段階では、一定フレームごとにOCRを実行する簡易的な実装。

        Returns:
            dict: 抽出したターンごとの情報のリストを含む辞書
        """
        if not os.path.exists(self.video_path):
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video file: {self.video_path}")

        frame_count = 0
        extracted_states = []
        prev_frame_gray = None
        
        # フレーム間の差分を計算するための閾値
        change_threshold = 1000000 # この値は動画の解像度や内容に応じて調整が必要

        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps == 0:
            fps = 30 # FPSが取得できない場合のデフォルト値

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        while frame_count < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            ret, frame = cap.read()
            if not ret:
                break

            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_gray = cv2.GaussianBlur(frame_gray, (21, 21), 0)

            if prev_frame_gray is not None:
                frame_delta = cv2.absdiff(prev_frame_gray, frame_gray)
                diff_score = frame_delta.sum()

                if diff_score > change_threshold:
                    print(f"Significant change detected at frame {frame_count} (diff: {diff_score})")
                    state = self.parser.parse_frame(frame)
                    if state and any(state.values()): # 何かしらのOCR結果があれば追加
                        extracted_states.append({
                            "frame": frame_count,
                            "state": state
                        })
            
            prev_frame_gray = frame_gray
            # 次の処理対象フレームをFPS分だけ進める（約1秒ごと）
            frame_count += fps

        cap.release()
        print(f"Video analysis complete. Total frames: {frame_count}. Extracted states: {len(extracted_states)}")

        # 抽出したstateから対戦ログを再構築
        reconstructed_log = self.reconstructor.reconstruct(extracted_states)

        # TODO: DatabaseManagerを使ってDBに保存する

        return reconstructed_log