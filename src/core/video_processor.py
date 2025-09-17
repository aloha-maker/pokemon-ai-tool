import cv2
import os
from src.core.ocr import GameStateParser
from src.database.manager import DatabaseManager

class VideoProcessor:
    """
    動画ファイルを解析して、対戦ログを抽出するクラス。
    """
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.parser = GameStateParser()

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
        # 2秒に1回程度の頻度でフレームを処理 (30fps想定)
        frame_interval = 60 
        
        extracted_states = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                print(f"Processing frame {frame_count}...")
                state = self.parser.parse_frame(frame)
                if state and state.get('my_pokemon_name'): # 何か意味のある情報が取れたら記録
                    extracted_states.append({
                        "frame": frame_count,
                        "state": state
                    })

            frame_count += 1

        cap.release()
        print(f"Video analysis complete. Total frames: {frame_count}. Extracted states: {len(extracted_states)}")

        # TODO: 抽出した複数のstateから、意味のあるターン情報を再構築するロジックを実装
        # TODO: DatabaseManagerを使ってDBに保存する

        return {"processed_frames": len(extracted_states), "log": extracted_states}
