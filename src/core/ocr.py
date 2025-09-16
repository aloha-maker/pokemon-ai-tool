import cv2
import pytesseract
import numpy as np
import json
import os

# Tesseractの実行ファイルのパスを指定 (Windowsの場合)
# Mac/Linuxの場合は不要なことが多い
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

class GameStateParser:
    """
    キャプチャしたゲーム画面から盤面情報を抽出・構造化するクラス。
    """
    def __init__(self, roi_config_path='roi_config.json'):
        """
        Args:
            roi_config_path (str): ROI設定が記述されたJSONファイルのパス。
        """
        self.rois = self._load_rois(roi_config_path)

    def _load_rois(self, path: str) -> dict:
        "ROI設定ファイルを読み込む。"
        if not os.path.exists(path):
            print(f"警告: ROI設定ファイル '{path}' が見つかりません。ROIは空になります。")
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"警告: ROI設定ファイル '{path}' の解析に失敗しました。ROIは空になります。")
            return {}
        except Exception as e:
            print(f"警告: ROI設定ファイル '{path}' の読み込み中に予期せぬエラーが発生しました: {e}")
            return {}

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

        if not self.rois:
            print("エラー: ROIが設定されていません。roi_config.jsonを確認してください。")
            return {}

        game_state = {}

        for key, roi in self.rois.items():
            # ROIが単一の座標リストの場合 (名前、HPなど)
            if isinstance(roi, list) and len(roi) == 4:
                try:
                    x, y, w, h = map(int, roi)
                    # ROIを切り出し
                    cropped_img = frame[y:y+h, x:x+w]
                    
                    # 前処理を適用
                    preprocessed_img = self._preprocess_image_for_ocr(cropped_img)
                    
                    # OCRを実行 (日本語を指定)
                    config = '--psm 7 -l jpn' # psm 7: 1行として認識
                    text = pytesseract.image_to_string(preprocessed_img, config=config).strip()
                    
                    game_state[key] = text
                except Exception as e:
                    print(f"エラー: ROI '{key}' の処理中にエラーが発生しました: {e}")
                    game_state[key] = "Error"
            
            # ROIが座標リストのリストの場合 (技リストなど)
            elif isinstance(roi, list):
                texts = []
                for i, r in enumerate(roi):
                    try:
                        x, y, w, h = map(int, r)
                        cropped_img = frame[y:y+h, x:x+w]
                        preprocessed_img = self._preprocess_image_for_ocr(cropped_img)
                        config = '--psm 7 -l jpn'
                        text = pytesseract.image_to_string(preprocessed_img, config=config).strip()
                        texts.append(text)
                    except Exception as e:
                        print(f"エラー: ROI '{key}' の要素 {i} の処理中にエラーが発生しました: {e}")
                        texts.append("Error")
                game_state[key] = texts

        return game_state
