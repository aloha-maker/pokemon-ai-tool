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
        self.reference_resolution, self.rois = self._load_rois(roi_config_path)

    def _load_rois(self, path: str) -> tuple[dict | None, dict]:
        """ROI設定ファイルを読み込み、基準解像度とROIの辞書を返す。"""
        if not os.path.exists(path):
            print(f"警告: ROI設定ファイル '{path}' が見つかりません。ROIは空になります。")
            return None, {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                ref_res = config.pop('reference_resolution', None)
                return ref_res, config
        except json.JSONDecodeError:
            print(f"警告: ROI設定ファイル '{path}' の解析に失敗しました。ROIは空になります。")
            return None, {}
        except Exception as e:
            print(f"警告: ROI設定ファイル '{path}' の読み込み中に予期せぬエラーが発生しました: {e}")
            return None, {}

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

    def _scale_roi(self, roi: tuple, scale_w: float, scale_h: float) -> tuple:
        """ROI座標をフレームサイズに合わせてスケーリングする。"""
        x, y, w, h = roi
        scaled_x = int(x * scale_w)
        scaled_y = int(y * scale_h)
        scaled_w = int(w * scale_w)
        scaled_h = int(h * scale_h)
        return (scaled_x, scaled_y, scaled_w, scaled_h)

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

        frame_h, frame_w = frame.shape[:2]

        # スケーリング係数を計算
        if self.reference_resolution:
            ref_w = self.reference_resolution.get("width", frame_w)
            ref_h = self.reference_resolution.get("height", frame_h)
            scale_w = frame_w / ref_w
            scale_h = frame_h / ref_h
        else:
            # 基準解像度がなければスケーリングしない
            scale_w, scale_h = 1.0, 1.0

        game_state = {}

        for key, roi_orig in self.rois.items():
            # ROIが単一の座標リストの場合 (名前、HPなど)
            if isinstance(roi_orig, list) and len(roi_orig) == 4:
                try:
                    # ROIをスケーリング
                    roi = self._scale_roi(tuple(roi_orig), scale_w, scale_h)
                    x, y, w, h = roi

                    # ROIがフレームの範囲内にあるかチェック
                    if x + w > frame_w or y + h > frame_h:
                        print(f"警告: ROI '{key}' が画像サイズ({frame_w}x{frame_h})を超えています。スキップします。")
                        game_state[key] = "Error: ROI out of bounds"
                        continue

                    # ROIを切り出し
                    cropped_img = frame[y:y+h, x:x+w]
                    
                    # 切り出した画像が空でないかチェック
                    if cropped_img.size == 0:
                        print(f"警告: ROI '{key}' で切り抜かれた画像が空です。スキップします。")
                        game_state[key] = "Error: Cropped image is empty"
                        continue

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
            elif isinstance(roi_orig, list):
                texts = []
                for i, r_orig in enumerate(roi_orig):
                    try:
                        # ROIをスケーリング
                        r = self._scale_roi(tuple(r_orig), scale_w, scale_h)
                        x, y, w, h = r

                        # ROIがフレームの範囲内にあるかチェック
                        if x + w > frame_w or y + h > frame_h:
                            print(f"警告: ROI '{key}[{i}]' が画像サイズ({frame_w}x{frame_h})を超えています。スキップします。")
                            texts.append("Error: ROI out of bounds")
                            continue

                        cropped_img = frame[y:y+h, x:x+w]

                        if cropped_img.size == 0:
                            print(f"警告: ROI '{key}[{i}]' で切り抜かれた画像が空です。スキップします。")
                            texts.append("Error: Cropped image is empty")
                            continue

                        preprocessed_img = self._preprocess_image_for_ocr(cropped_img)
                        config = '--psm 7 -l jpn'
                        text = pytesseract.image_to_string(preprocessed_img, config=config).strip()
                        texts.append(text)
                    except Exception as e:
                        print(f"エラー: ROI '{key}' の要素 {i} の処理中にエラーが発生しました: {e}")
                        texts.append("Error")
                game_state[key] = texts

        return game_state
