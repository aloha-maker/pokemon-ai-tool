import cv2
import pytesseract
import numpy as np

# Tesseractの実行ファイルのパスを指定 (Windowsの場合)
# Mac/Linuxの場合は不要なことが多い
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class GameStateParser:
    """
    キャプチャしたゲーム画面から盤面情報を抽出・構造化するクラス。
    """
    def __init__(self):
        # 【重要】各情報が画面のどこに表示されるかを定義する
        # (x, y, width, height) の形式
        self.rois = {
            "my_pokemon_name": (100, 300, 200, 50),
            "my_pokemon_hp": (120, 350, 150, 40),
            "opponent_pokemon_name": (600, 50, 200, 50),
            "moves_list": [(500, 400, 250, 50) for i in range(4)] # 技4つ分など
        }

    def _preprocess_image_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """
        OCRの精度を向上させるための画像前処理。
        """
        # 1. グレースケール化
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. 二値化（背景と文字をくっきり分ける）
        #    Adaptive Thresholdingは、照明が均一でない場合に特に有効
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return binary

    def parse_frame(self, frame: np.ndarray) -> dict:
        """
        単一のフレームを解析し、構造化された盤面情報を返す。

        Args:
            frame (np.ndarray): ScreenCapturerから取得した画像フレーム。

        Returns:
            dict: 抽出した盤面情報。
        """
        if frame is None:
            return {}

        game_state = {}

        for key, roi in self.rois.items():
            # ROIが単一の場合 (名前、HPなど)
            if isinstance(roi, tuple):
                x, y, w, h = roi
                # ROIを切り出し
                cropped_img = frame[y:y+h, x:x+w]
                
                # 前処理を適用
                preprocessed_img = self._preprocess_image_for_ocr(cropped_img)
                
                # OCRを実行 (日本語を指定)
                config = '--psm 7 -l jpn' # psm 7: 1行として認識
                text = pytesseract.image_to_string(preprocessed_img, config=config).strip()
                
                game_state[key] = text
            
            # ROIがリストの場合 (技リストなど)
            elif isinstance(roi, list):
                texts = []
                for r in roi:
                    x, y, w, h = r
                    cropped_img = frame[y:y+h, x:x+w]
                    preprocessed_img = self._preprocess_image_for_ocr(cropped_img)
                    config = '--psm 7 -l jpn'
                    text = pytesseract.image_to_string(preprocessed_img, config=config).strip()
                    texts.append(text)
                game_state[key] = texts

        return game_state
