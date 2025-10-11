import cv2
import os
import json
import shutil
import hashlib
from glob import glob
import pytesseract
from PIL import Image
import re
import pandas as pd
import numpy as np

INPUT_DIR = r'C:\pokemon-ai-tool\.traindata\video\input_videos'
OUTPUT_DIR = r'C:\pokemon-ai-tool\.traindata\text2img'
PROCESSED_DIR = r'C:\pokemon-ai-tool\.traindata\video\processed_videos'
ROI_FILE = r'C:\pokemon-ai-tool\instance\roi_config.json'
POKEMON_MASTER_PATH = r'C:\pokemon-ai-tool\data\master_data\pokemons.csv'
ABILITY_MASTER_PATH = r'C:\pokemon-ai-tool\data\master_data\abilities.csv'
EXTRACT_PER_SECOND = 0.3  # 1秒に3枚抽出

# OCR対象外のROIリスト（画像は保存するがOCR処理はしない）
OCR_EXEMPT_ROIS = {'your_ailment', 'my_ailment', 'my_pokemon_hp', 'opponent_pokemon_hp'}

# OCR対象外のROIリスト（完全にスキップ）
SKIP_ROIS = {'your_party'} | {f'your_poke{i}' for i in range(1, 7)}

# ポケモン名ROI
POKEMON_NAME_ROIS = {'my_pokemon_name', 'opponent_pokemon_name'}

# HP ROI（画像のみ保存、ポケモン名ROIが確信度90以上の場合のみ）
HP_ROIS = {'my_pokemon_hp', 'opponent_pokemon_hp'}

# 状態異常ROI（画像のみ保存、ポケモン名ROIが確信度90以上の場合のみ）
AILMENT_ROIS = {'my_ailment', 'your_ailment'}

# その他のROI
OTHER_ROIS = {
    'live_comment_row1', 'live_comment_row2', 
    'my_tokusei_row1', 'my_tokusei_row2', 
    'your_tokusei_row1', 'your_tokusei_row2'
}

# 特性名補正対象のROI
ABILITY_NAME_ROIS = {'my_tokusei_row2', 'your_tokusei_row2'}

# 「ポケモン名+の」形式に変換するROI
POKEMON_NO_ROIS = {'my_tokusei_row1', 'your_tokusei_row1'}

def win_safe_path(path):
    if os.name == 'nt':
        return "\\\\?\\" + os.path.abspath(path)
    return path

with open(ROI_FILE, "r", encoding="utf-8") as f:
    roi_dict = json.load(f)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Tesseractの設定
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# tessdata_custom へのパス設定
script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
tessdata_dir = os.path.join(project_root, "tessdata_custom")
custom_config = f"--tessdata-dir {tessdata_dir} --oem 3 --psm 7"

class NameCorrector:
    """名前補正の基底クラス"""
    
    def __init__(self, master_path, column_name):
        self.names = self._load_names(master_path, column_name)
    
    def _load_names(self, path, column_name):
        """マスターファイルから名前のリストを読み込む"""
        if not os.path.exists(path):
            print(f"警告: マスターファイル '{path}' が見つかりません。名前補正は無効になります。")
            return []
        try:
            df = pd.read_csv(path)
            # 指定されたカラムから名前リストを取得
            return [name for name in df[column_name].unique() if pd.notna(name)]
        except Exception as e:
            print(f"警告: マスターファイル '{path}' の読み込み中にエラーが発生しました: {e}")
            return []
    
    def _levenshtein_distance(self, s1, s2):
        """2つの文字列間のレーベンシュタイン距離を計算する"""
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
    
    def find_closest_name(self, text, threshold=2):
        """
        OCRで読み取ったテキストに最も近い名前を辞書から探す
        閾値以下の距離で見つからない場合は元のテキストを返す
        """
        if not self.names or not text:
            return text

        # 完全一致があればそれを返す
        if text in self.names:
            return text

        # 最も距離が近い名前を見つける
        closest_name = min(self.names, key=lambda name: self._levenshtein_distance(text, name))
        min_distance = self._levenshtein_distance(text, closest_name)

        # 閾値チェック
        if min_distance <= threshold:
            return closest_name
        else:
            return text

class PokemonNameCorrector(NameCorrector):
    """ポケモン名の補正クラス"""
    def __init__(self, pokemon_master_path):
        super().__init__(pokemon_master_path, 'name_ja')

class AbilityNameCorrector(NameCorrector):
    """特性名の補正クラス"""
    def __init__(self, ability_master_path):
        super().__init__(ability_master_path, 'name_ja')

class OCRProcessor:
    def __init__(self, pokemon_corrector, ability_corrector):
        self.pokemon_corrector = pokemon_corrector
        self.ability_corrector = ability_corrector
        # 直前のポケモン名を保持する変数
        self.last_my_pokemon_name = ""
        self.last_opponent_pokemon_name = ""

    @staticmethod
    def preprocess_image(image):
        """
        画像の前処理を行う
        """
        if image is None or image.size == 0:
            return None

        # グレースケール変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # ノイズ除去
        denoised = cv2.medianBlur(gray, 3)

        # 二値化（大津の方法）
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def extract_text_from_image(self, image, roi_name):
        """
        画像からテキストと確信度統計を抽出する
        """
        processed_image = self.preprocess_image(image)
        if processed_image is None:
            return "", {"max": 0, "median": 0, "avg": 0}

        try:
            data = pytesseract.image_to_data(
                processed_image,
                config=custom_config,
                lang='jpn+jpn_pokemon',
                output_type=pytesseract.Output.DICT
            )

            # テキスト結合
            text = " ".join([t for t in data['text'] if t.strip() != ""])
            cleaned_text = self.clean_text(text)

            # 確信度の統計計算
            conf_values = [float(c) for c in data['conf'] if c != '-1']
            if conf_values:
                max_conf = max(conf_values)
                median_conf = sorted(conf_values)[len(conf_values) // 2]
                avg_conf = sum(conf_values) / len(conf_values)
            else:
                max_conf = median_conf = avg_conf = 0.0

            conf_stats = {
                "max": max_conf,
                "median": median_conf,
                "avg": avg_conf
            }

            return cleaned_text, conf_stats

        except Exception as e:
            print(f"エラー: OCR処理中に問題が発生: {e}")
            return "", {"max": 0, "median": 0, "avg": 0}

    def apply_name_correction(self, text, roi_name):
        """
        名前の補正を適用する（確信度90以上の場合のみ）
        """
        if roi_name in POKEMON_NAME_ROIS:
            original_text = text
            corrected_text = self.pokemon_corrector.find_closest_name(text)
            if original_text != corrected_text:
                print(f"  ポケモン名補正: '{original_text}' -> '{corrected_text}'")
            
            # ポケモン名を保持（後の「〜の」変換用）
            if roi_name == 'my_pokemon_name':
                self.last_my_pokemon_name = corrected_text
            elif roi_name == 'opponent_pokemon_name':
                self.last_opponent_pokemon_name = corrected_text
                
            return corrected_text
        
        elif roi_name in ABILITY_NAME_ROIS:
            original_text = text
            corrected_text = self.ability_corrector.find_closest_name(text)
            if original_text != corrected_text:
                print(f"  特性名補正: '{original_text}' -> '{corrected_text}'")
            return corrected_text
        
        elif roi_name in POKEMON_NO_ROIS:
            # 「ポケモン名+の」形式に変換
            return self._convert_to_pokemon_no_format(text, roi_name)
        
        return text

    def _convert_to_pokemon_no_format(self, text, roi_name):
        """
        「ポケモン名+の」形式に変換する
        """
        # 対応するポケモン名を取得
        if roi_name == 'my_tokusei_row1':
            pokemon_name = self.last_my_pokemon_name
        elif roi_name == 'your_tokusei_row1':
            pokemon_name = self.last_opponent_pokemon_name
        else:
            return text

        # ポケモン名が空の場合は変換しない
        if not pokemon_name:
            return text

        # 既に「〜の」形式かチェック
        if text.endswith('の'):
            # 既に「の」が付いている場合はそのまま返す
            return text
        else:
            # ポケモン名 + 「の」に変換
            converted_text = f"{pokemon_name}の"
            if text != converted_text:
                print(f"  「〜の」形式変換: '{text}' -> '{converted_text}'")
            return converted_text

    @staticmethod
    def clean_text(text):
        """
        抽出したテキストをクリーニングする
        """
        # 空白文字（スペース、改行など）をすべて削除
        cleaned_text = re.sub(r"\s+", "", text)

        # 連続するハイフンを単一のハイフンに
        cleaned_text = re.sub(r"-+", "-", cleaned_text)
        
        # 「/」を「！」に変換
        cleaned_text = cleaned_text.replace("/", "！")

        return cleaned_text

    def detect_text_with_ocr(self, image, roi_name):
        """
        OCRを使用してテキストの有無と確信度を判定
        """
        extracted_text, conf_stats = self.extract_text_from_image(image, roi_name)
        max_conf = conf_stats["max"]
        has_text = max_conf >= 90 and extracted_text
        
        return has_text, extracted_text, conf_stats

    def process_roi_with_confidence_check(self, frame, roi_name, value, width, height, video_name, frame_idx, short_hash):
        """
        指定されたROIを処理し、確信度に基づいて保存する
        """
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, 0

        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, 0

        roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
        save_path = win_safe_path(os.path.join(roi_dir, filename))

        # HP ROIと状態異常ROIの場合はOCR処理せずに画像のみ保存
        if roi_name in HP_ROIS or roi_name in AILMENT_ROIS:
            # 画像を保存
            if not cv2.imwrite(save_path, roi_img):
                print(f"⚠ 保存失敗: {save_path}")
                return False, 0
            
            roi_type = "HP ROI" if roi_name in HP_ROIS else "状態異常 ROI"
            print(f"📷 {roi_name}_{frame_idx:06d} ({roi_type} - 画像のみ保存)")
            return True, 0

        # その他のROIはOCR処理
        has_text, extracted_text, conf_stats = self.detect_text_with_ocr(roi_img, roi_name)
        max_conf = conf_stats["max"]

        if has_text:
            # 確信度90以上の場合、テキスト処理を適用
            extracted_text = self.apply_name_correction(extracted_text, roi_name)

            # 画像を保存
            if not cv2.imwrite(save_path, roi_img):
                print(f"⚠ 保存失敗: {save_path}")
                return False, max_conf

            # テキストファイルを作成（確信度情報なし）
            text_file_name = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
            text_file_path = win_safe_path(os.path.join(roi_dir, text_file_name))

            max_conf_int = int(conf_stats["max"])

            # テキストファイルにはテキストのみ書き込み（確信度情報なし）
            with open(text_file_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)

            # コンソールには確信度情報を出力
            print(f"✓ {roi_name}_{frame_idx:06d}: '{extracted_text}' (確信度: {max_conf_int})")
            return True, max_conf
        else:
            # 確信度90未満の場合、画像を削除（保存しない）
            print(f"✗ {roi_name}_{frame_idx:06d} (確信度 {max_conf:.1f} < 90 → 保存せず)")
            return False, max_conf

    def save_supplementary_roi_images(self, frame, video_name, frame_idx, short_hash, width, height):
        """
        補助ROI（HPと状態異常）の画像を保存する（ポケモン名ROIが確信度90以上の場合のみ呼び出される）
        """
        supplementary_save_count = 0
        
        # HP ROIと状態異常ROIを保存
        for roi_name in HP_ROIS.union(AILMENT_ROIS):
            if roi_name not in roi_dict:
                continue
                
            value = roi_dict[roi_name]
            if not (isinstance(value, list) and len(value) == 4):
                continue

            x, y, w, h = value
            if x + w > width or y + h > height:
                continue

            roi_img = frame[y:y+h, x:x+w]
            if roi_img.size == 0:
                continue

            roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
            os.makedirs(roi_dir, exist_ok=True)
            filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
            save_path = win_safe_path(os.path.join(roi_dir, filename))

            # 補助ROIの画像を保存
            if not cv2.imwrite(save_path, roi_img):
                print(f"⚠ 補助ROI保存失敗: {save_path}")
                continue
            
            roi_type = "HP ROI" if roi_name in HP_ROIS else "状態異常 ROI"
            print(f"📷 {roi_name}_{frame_idx:06d} ({roi_type} - 画像のみ保存)")
            supplementary_save_count += 1
        
        return supplementary_save_count

def process_video(video_path, pokemon_corrector, ability_corrector, ocr_processor):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    print(f"\n▶ 動画処理開始: {video_name}")

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

    # フレーム処理前に直前のポケモン名をリセット
    ocr_processor.last_my_pokemon_name = ""
    ocr_processor.last_opponent_pokemon_name = ""

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            print(f"  📊 フレーム {frame_idx}: 処理開始")
            
            processed_pokemon = False
            pokemon_success = False
            
            # ステップ1: ポケモン名ROIを優先処理
            for roi_name in POKEMON_NAME_ROIS:
                if roi_name not in roi_dict or roi_name in SKIP_ROIS:
                    continue
                    
                value = roi_dict[roi_name]
                if not (isinstance(value, list) and len(value) == 4):
                    continue

                success, max_conf = ocr_processor.process_roi_with_confidence_check(
                    frame, roi_name, value, width, height, video_name, frame_idx, short_hash
                )
                
                if success:
                    pokemon_success = True
                    save_count += 1
                    ocr_success_count += 1
                    processed_pokemon = True
            
            # ステップ1a: ポケモン名ROIが確信度90以上の場合、補助ROI（HPと状態異常）も保存
            if pokemon_success:
                supplementary_save_count = ocr_processor.save_supplementary_roi_images(frame, video_name, frame_idx, short_hash, width, height)
                save_count += supplementary_save_count
                print(f"  💚 ポケモン名ROI成功に伴い、補助ROI {supplementary_save_count}枚を保存")
            
            # ステップ2: ポケモン名ROIの確信度が低い場合、他のROIを処理（補助ROIは処理しない）
            if not pokemon_success:
                print(f"  🔄 ポケモン名ROI確信度不足、他のROIを処理（補助ROIは処理しない）")
                
                for roi_name in OTHER_ROIS:  # 補助ROIは含めない
                    if (roi_name not in roi_dict or 
                        roi_name in SKIP_ROIS or 
                        roi_name in OCR_EXEMPT_ROIS):
                        continue
                        
                    value = roi_dict[roi_name]
                    if not (isinstance(value, list) and len(value) == 4):
                        continue

                    success, max_conf = ocr_processor.process_roi_with_confidence_check(
                        frame, roi_name, value, width, height, video_name, frame_idx, short_hash
                    )
                    
                    if success:
                        save_count += 1
                        ocr_success_count += 1
                        processed_pokemon = True
            
            if not processed_pokemon:
                print(f"  ⏭️ フレーム {frame_idx}: 有効なROIなし（スキップ）")

        frame_idx += 1

    cap.release()
    print(f"✅ {video_name} 処理完了（保存画像数: {save_count}, OCR成功: {ocr_success_count}）")
    
    # 処理済み動画を移動
    try:
        shutil.move(video_path, os.path.join(PROCESSED_DIR, os.path.basename(video_path)))
    except Exception as e:
        print(f"⚠ 動画移動失敗: {e}")

def main():
    print("動画からの画像抽出＋OCR処理を開始します...")
    print("設定:")
    print(f"  入力ディレクトリ: {INPUT_DIR}")
    print(f"  出力ディレクトリ: {OUTPUT_DIR}")
    print(f"  処理済みディレクトリ: {PROCESSED_DIR}")
    print(f"  抽出間隔: {EXTRACT_PER_SECOND}枚/秒")
    print(f"  OCR対象外ROI: {OCR_EXEMPT_ROIS}")
    print(f"  スキップ対象ROI: {SKIP_ROIS}")
    print(f"  ポケモン名ROI: {POKEMON_NAME_ROIS}")
    print(f"  HP ROI (ポケモン名成功時のみ画像保存): {HP_ROIS}")
    print(f"  状態異常 ROI (ポケモン名成功時のみ画像保存): {AILMENT_ROIS}")
    print(f"  その他ROI: {OTHER_ROIS}")
    print(f"  特性名補正対象: {ABILITY_NAME_ROIS}")
    print(f"  「〜の」形式変換対象: {POKEMON_NO_ROIS}")
    print()

    # ポケモン名補正器の初期化
    pokemon_corrector = PokemonNameCorrector(POKEMON_MASTER_PATH)
    ability_corrector = AbilityNameCorrector(ABILITY_MASTER_PATH)
    ocr_processor = OCRProcessor(pokemon_corrector, ability_corrector)

    # 補正機能の状態表示
    if pokemon_corrector.names:
        print(f"✅ ポケモン名補正機能: 有効 ({len(pokemon_corrector.names)}種類)")
    else:
        print("⚠ ポケモン名補正機能: 無効")

    if ability_corrector.names:
        print(f"✅ 特性名補正機能: 有効 ({len(ability_corrector.names)}種類)")
    else:
        print("⚠ 特性名補正機能: 無効")

    print(f"✅ 「〜の」形式変換機能: 有効 ({POKEMON_NO_ROIS})")
    print(f"✅ HP ROI画像保存機能: 有効 ({HP_ROIS})")
    print(f"✅ 状態異常 ROI画像保存機能: 有効 ({AILMENT_ROIS})")
    print("  ※確信度90以上の対象ROIのみ保存")
    print("  ※ポケモン名ROI優先 → 確信度不足時は他のROIを処理")
    print("  ※補助ROI（HP・状態異常）はポケモン名ROI成功時のみ保存")
    print("  ※テキストファイルには確信度情報を出力しない")
    print("  ※「/」を「！」に変換")

    while True:
        video_files = glob(os.path.join(INPUT_DIR, "*.mp4"))
        if not video_files:
            print("\n🎉 全ての動画処理が完了しました。")
            break

        for video_file in video_files:
            process_video(video_file, pokemon_corrector, ability_corrector, ocr_processor)

if __name__ == "__main__":
    main()