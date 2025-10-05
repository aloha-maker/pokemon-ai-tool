import cv2
import pytesseract
import numpy as np
import json
import os
import pandas as pd

# Tesseractの実行ファイルのパスを指定 (Windowsの場合)
# Mac/Linuxの場合は不要なことが多い
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

class GameStateParser:
    """
    キャプチャしたゲーム画面から盤面情報を抽出・構造化するクラス。
    """
    def __init__(self, roi_config_path='instance/roi_config.json', pokemon_master_path='data/master_data/pokemons.csv'):
        """
        Args:
            roi_config_path (str): ROI設定が記述されたJSONファイルのパス。
            pokemon_master_path (str): ポケモンマスターデータが格納されたCSVファイルのパス。
        """
        self.reference_resolution, self.rois = self._load_rois(roi_config_path)
        self.pokemon_names = self._load_pokemon_names(pokemon_master_path)

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

    def _load_pokemon_names(self, path: str) -> list[str]:
        """ポケモンマスターCSVから日本語名のリストを読み込む。"""
        if not os.path.exists(path):
            print(f"警告: ポケモンマスターファイル '{path}' が見つかりません。名前補正は無効になります。")
            return []
        try:
            df = pd.read_csv(path)
            # カタカナと英字のみを考慮し、不要な文字を除去
            return [name for name in df['name_ja'].unique() if pd.notna(name)]
        except Exception as e:
            print(f"警告: ポケモンマスターファイル '{path}' の読み込み中にエラーが発生しました: {e}")
            return []

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """2つの文字列間のレーベンシュタイン距離を計算する。"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _find_closest_pokemon_name(self, text: str, threshold: int = 2) -> str:
        """
        OCRで読み取ったテキストに最も近いポケモン名を辞書から探す。
        閾値以下の距離で見つからない場合は元のテキストを返す。
        """
        if not self.pokemon_names or not text:
            return text

        # 完全一致があればそれを返す
        if text in self.pokemon_names:
            return text

        # 最も距離が近いポケモン名を見つける
        closest_name = min(self.pokemon_names, key=lambda name: self._levenshtein_distance(text, name))
        min_distance = self._levenshtein_distance(text, closest_name)

        # 閾値チェック
        if min_distance <= threshold:
            return closest_name
        else:
            return text

    def _preprocess_image_for_ocr(self, img: np.ndarray) -> np.ndarray:
        """
        OCRの精度を向上させるための画像前処理。
        """
        # 1. グレースケール化
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. 画像の拡大（アップスケーリング）
        #    補間方法には高品質なものを選択 (LANCZOS4 > CUBIC > LINEAR)
        height, width = gray.shape
        scale_factor = 2
        upscaled = cv2.resize(gray, (width * scale_factor, height * scale_factor), interpolation=cv2.INTER_CUBIC)

        # 3. ノイズ除去（メディアンフィルタ）
        #    カーネルサイズは奇数である必要があり、3や5が一般的。
        denoised = cv2.medianBlur(upscaled, 3)
        
        # 4. 二値化（背景と文字をくっきり分ける）
        #    Adaptive Thresholdingは、照明が均一でない場合に特に有効
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
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
                    
                    # OCRを実行 (日本語+カスタムモデルを指定)
                    # スクリプトの場所を基準にtessdata_customへの絶対パスを構築
                    script_path = os.path.abspath(__file__)
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
                    tessdata_dir = os.path.join(project_root, 'tessdata_custom')
                    config = f'--tessdata-dir {tessdata_dir} --psm 7 -l jpn+jpn_pokemon'
                    text = pytesseract.image_to_string(preprocessed_img, config=config).strip()

                    # ポケモン名フィールドの場合は補正を試みる
                    if key.endswith('_name'):
                        text = self._find_closest_pokemon_name(text)
                    
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
                        # OCRを実行 (日本語+カスタムモデルを指定)
                        # スクリプトの場所を基準にtessdata_customへの絶対パスを構築
                        script_path = os.path.abspath(__file__)
                        project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
                        tessdata_dir = os.path.join(project_root, 'tessdata_custom')
                        config = f'--tessdata-dir {tessdata_dir} --psm 7 -l jpn+jpn_pokemon'
                        text = pytesseract.image_to_string(preprocessed_img, config=config).strip()
                        texts.append(text)
                    except Exception as e:
                        print(f"エラー: ROI '{key}' の要素 {i} の処理中にエラーが発生しました: {e}")
                        texts.append("Error")
                game_state[key] = texts

        return game_state


class PokemonRecognizer:
    """
    テンプレートマッチングを用いて、画像からポケモンを認識するクラス。
    """
    STANDARD_SIZE = (96, 96)  # 比較用の標準サイズ

    def __init__(self, template_dir='data/pokemon_images', threshold=0.8):
        """
        Args:
            template_dir (str): ポケモンのテンプレート画像が格納されているディレクトリ。
            threshold (float): テンプレートマッチングの類似度スコアの閾値。
        """
        self.template_dir = template_dir
        self.threshold = threshold
        self.templates = self._load_templates()

    def _load_templates(self):
        """テンプレート画像をメモリに読み込み、標準サイズにリサイズする。"""
        templates = {}
        if not os.path.isdir(self.template_dir):
            print(f"警告: テンプレートディレクトリ '{self.template_dir}' が見つかりません。")
            return templates

        for pokemon_name in os.listdir(self.template_dir):
            pokemon_dir = os.path.join(self.template_dir, pokemon_name)
            if os.path.isdir(pokemon_dir):
                image_files = [f for f in os.listdir(pokemon_dir) if f.endswith(('.png', '.jpg'))]
                if image_files:
                    template_path = os.path.join(pokemon_dir, image_files[0])
                    try:
                        # 日本語パス対応
                        with open(template_path, 'rb') as f:
                            img_binary = np.fromfile(f, dtype=np.uint8)
                        template_img = cv2.imdecode(img_binary, cv2.IMREAD_GRAYSCALE)
                        
                        if template_img is not None:
                            # 標準サイズにリサイズして保持
                            resized_template = cv2.resize(template_img, self.STANDARD_SIZE, interpolation=cv2.INTER_AREA)
                            templates[pokemon_name] = resized_template
                        else:
                            print(f"警告: テンプレート画像をデコードできませんでした: {template_path}")

                    except Exception as e:
                        print(f"警告: テンプレート画像の読み込みに失敗しました: {template_path}, エラー: {e}")
                        
        print(f"{len(templates)}個のポケモンテンプレートを読み込みました。")
        return templates

    def recognize(self, image: np.ndarray) -> dict:
        """
        単一の画像から最も一致するポケモンの情報を返す。

        Args:
            image (np.ndarray): 認識対象の画像 (ROIから切り抜かれたもの)。

        Returns:
            dict: 認識結果の情報を含む辞書。
                  {'name': str, 'score': float, 'template_name': str}
        """
        if image is None or image.size == 0 or not self.templates:
            return {"name": "", "score": 0.0, "template_name": ""}

        # 入力画像をグレースケールに変換し、標準サイズにリサイズ
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized_image = cv2.resize(gray_image, self.STANDARD_SIZE, interpolation=cv2.INTER_AREA)

        best_match = {"name": "", "score": 0.0, "template_name": ""}

        for name, template in self.templates.items():
            res = cv2.matchTemplate(resized_image, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)

            if max_val > best_match["score"]:
                best_match["template_name"] = name
                best_match["score"] = float(max_val)

        # 閾値を超えていれば、認識成功とする
        if best_match["score"] >= self.threshold:
            best_match["name"] = best_match["template_name"]

        return best_match
