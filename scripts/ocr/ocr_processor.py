import os
import cv2
import re
import pytesseract
from config import (
    OUTPUT_DIR, HP_ROIS, AILMENT_ROIS, POKEMON_NAME_ROIS,
    ABILITY_NAME_ROIS, POKEMON_NO_ROIS, ROI_DICT, CUSTOM_CONFIG,
    TESSERACT_PATH
)
from utils import win_safe_path
from aliment_ocv import identify_ailment_from_cropped_image


class OCRProcessor:
    def __init__(self, pokemon_corrector, ability_corrector):
        self.pokemon_corrector = pokemon_corrector
        self.ability_corrector = ability_corrector

        # 直前のポケモン名を保持
        self.last_my_pokemon_name = ""
        self.last_opponent_pokemon_name = ""

        # Tesseract設定
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        # 状態異常アイコンフォルダのパス
        self.ailment_icons_dir = r'C:\pokemon-ai-tool\static\ailment_icons'

    # ==========================
    # 画像前処理
    # ==========================
    @staticmethod
    def preprocess_image(image):
        """OCR前のノイズ除去・二値化"""
        if image is None or image.size == 0:
            return None

        # グレースケール
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # ノイズ除去
        denoised = cv2.medianBlur(gray, 3)

        # 大津の方法で二値化
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary

    # ==========================
    # OCR実行
    # ==========================
    def extract_text_from_image(self, image, roi_name):
        """画像から文字列と確信度を抽出"""
        processed = self.preprocess_image(image)
        if processed is None:
            return "", {"max": 0, "median": 0, "avg": 0}

        try:
            data = pytesseract.image_to_data(
                processed,
                config=CUSTOM_CONFIG,
                lang='jpn+jpn_pokemon',
                output_type=pytesseract.Output.DICT
            )

            text = " ".join([t for t in data['text'] if t.strip()])
            cleaned_text = self.clean_text(text)

            conf_values = [float(c) for c in data['conf'] if c != '-1']
            if conf_values:
                max_conf = max(conf_values)
                median_conf = sorted(conf_values)[len(conf_values)//2]
                avg_conf = sum(conf_values) / len(conf_values)
            else:
                max_conf = median_conf = avg_conf = 0.0

            return cleaned_text, {"max": max_conf, "median": median_conf, "avg": avg_conf}

        except Exception as e:
            print(f"⚠ OCR処理エラー: {e}")
            return "", {"max": 0, "median": 0, "avg": 0}

    # ==========================
    # テキスト補正
    # ==========================
    def apply_name_correction(self, text, roi_name):
        """OCR後の文字列をマスターデータに基づいて補正"""
        if roi_name in POKEMON_NAME_ROIS:
            original_text = text
            corrected_text = self.pokemon_corrector.find_closest_name(text)
            if original_text != corrected_text:
                print(f"  🟢 ポケモン名補正: '{original_text}' → '{corrected_text}'")

            if roi_name == 'my_pokemon_name':
                self.last_my_pokemon_name = corrected_text
            elif roi_name == 'opponent_pokemon_name':
                self.last_opponent_pokemon_name = corrected_text
            return corrected_text

        elif roi_name in ABILITY_NAME_ROIS:
            original_text = text
            corrected_text = self.ability_corrector.find_closest_name(text)
            if original_text != corrected_text:
                print(f"  🔵 特性名補正: '{original_text}' → '{corrected_text}'")
            return corrected_text

        elif roi_name in POKEMON_NO_ROIS:
            return self._convert_to_pokemon_no_format(text, roi_name)

        return text

    def _convert_to_pokemon_no_format(self, text, roi_name):
        """「ポケモン名+の」形式への変換"""
        if roi_name == 'my_tokusei_row1':
            pokemon_name = self.last_my_pokemon_name
        elif roi_name == 'your_tokusei_row1':
            pokemon_name = self.last_opponent_pokemon_name
        else:
            return text

        if not pokemon_name:
            return text
        if text.endswith('の'):
            return text

        converted_text = f"{pokemon_name}の"
        if text != converted_text:
            print(f"  💫 「〜の」形式変換: '{text}' → '{converted_text}'")
        return converted_text

    # ==========================
    # テキストクリーニング
    # ==========================
    @staticmethod
    def clean_text(text):
        """空白削除・記号統一・誤字修正"""
        # 空白削除
        cleaned = re.sub(r"\s+", "", text)

        # 記号統一
        cleaned = re.sub(r"-+", "-", cleaned)
        cleaned = cleaned.replace("/", "！")

        # 誤字修正パターン
        # 八→ハ/パ/バ
        cleaned = re.sub(r'八', 'ハ', cleaned)

        # 丸数字→通常数字
        cleaned = cleaned.replace('①', '1')
        cleaned = cleaned.replace('②', '2')
        cleaned = cleaned.replace('③', '3')
        cleaned = cleaned.replace('④', '4')
        cleaned = cleaned.replace('⑤', '5')

        # 重複表現の修正
        cleaned = cleaned.replace('ただた！', 'た！')

        # 誤字修正
        cleaned = cleaned.replace('ぐりだした！', 'くりだした！')

        return cleaned

    # ==========================
    # OCR確信度チェック
    # ==========================
    def detect_text_with_ocr(self, image, roi_name):
        text, conf = self.extract_text_from_image(image, roi_name)
        max_conf = conf["max"]
        has_text = max_conf >= 90 and text
        return has_text, text, conf

    # ==========================
    # ROIごとのOCR処理+保存
    # ==========================
    def process_roi_with_confidence_check(self, frame, roi_name, value,
                                          width, height, video_name,
                                          frame_idx, short_hash):
        """ROI領域をOCR処理し、条件に応じて保存"""
        from hp_ocv import get_hp_percentage  # HPバー処理追加

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

        # ROI画像保存
        if not cv2.imwrite(save_path, roi_img):
            print(f"⚠ 保存失敗: {save_path}")
            return False, 0

        # =============================
        # HPバー処理(HP_ROIS)
        # =============================
        if roi_name in HP_ROIS:
            try:
                hp_percent = get_hp_percentage(save_path)
                text_file_name = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
                text_file_path = win_safe_path(os.path.join(roi_dir, text_file_name))
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(f"{hp_percent:.2f}")
                print(f"📊 {roi_name}_{frame_idx:06d}: HP {hp_percent:.2f}% を出力")
                return True, 0
            except Exception as e:
                print(f"⚠ HPバー処理エラー: {e}")
                return False, 0

        # =============================
        # 状態異常ROI(画像+状態異常判別)
        # =============================
        if roi_name in AILMENT_ROIS:
            try:
                ailment_result = identify_ailment_from_cropped_image(
                    save_path,
                    self.ailment_icons_dir,
                    threshold=0.8
                )
                
                # 状態異常が検出されなかった場合は画像とテキストを削除して終了
                if not ailment_result:
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    print(f"⚪ {roi_name}_{frame_idx:06d}: 状態異常なし (保存せず)")
                    return False, 0
                
                # 状態異常が検出された場合のみテキストファイルを出力
                text_file_name = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
                text_file_path = win_safe_path(os.path.join(roi_dir, text_file_name))
                
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(ailment_result)
                
                print(f"🔴 {roi_name}_{frame_idx:06d}: 状態異常 '{ailment_result}' を出力")
                return True, 0
            except Exception as e:
                print(f"⚠ 状態異常処理エラー: {e}")
                # エラー時は画像も削除
                if os.path.exists(save_path):
                    os.remove(save_path)
                return False, 0

        # =============================
        # OCR処理(通常ROI)
        # =============================
        has_text, text, conf = self.detect_text_with_ocr(roi_img, roi_name)
        max_conf = conf["max"]

        if has_text:
            text = self.apply_name_correction(text, roi_name)

            text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
            text_path = win_safe_path(os.path.join(roi_dir, text_filename))
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"✔ {roi_name}_{frame_idx:06d}: '{text}' (確信度: {int(max_conf)})")
            return True, max_conf
        else:
            print(f"✗ {roi_name}_{frame_idx:06d} (確信度 {max_conf:.1f} < 90 → 保存せず)")
            return False, max_conf


    # ==========================
    # HP・状態異常補助ROI保存
    # ==========================
    def save_supplementary_roi_images(self, frame, video_name,
                                    frame_idx, short_hash, width, height):
        """
        補助ROI(HPと状態異常)の画像を保存する
        HPバーの場合は数値を推定してテキストファイルも出力
        状態異常の場合は判別結果をテキストファイルに出力
        (ポケモン名ROIが確信度90以上で成功した場合のみ呼び出される)
        """
        from hp_ocv import get_hp_percentage  # HPバー解析を利用

        supplementary_save_count = 0

        for roi_name in HP_ROIS.union(AILMENT_ROIS):
            if roi_name not in ROI_DICT:
                continue

            value = ROI_DICT[roi_name]
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

            # --- 画像保存 ---
            if not cv2.imwrite(save_path, roi_img):
                print(f"⚠ 補助ROI保存失敗: {save_path}")
                continue

            # --- HPバーの場合 ---
            if roi_name in HP_ROIS:
                try:
                    hp_percent = get_hp_percentage(save_path)
                    text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
                    text_path = win_safe_path(os.path.join(roi_dir, text_filename))
                    with open(text_path, "w", encoding="utf-8") as f:
                        f.write(f"{hp_percent:.2f}")
                    print(f"📊 {roi_name}_{frame_idx:06d}: HP {hp_percent:.2f}% を出力")
                except Exception as e:
                    print(f"⚠ HPバー処理エラー ({roi_name}): {e}")

            # --- 状態異常ROIの場合 ---
            elif roi_name in AILMENT_ROIS:
                try:
                    ailment_result = identify_ailment_from_cropped_image(
                        save_path,
                        self.ailment_icons_dir,
                        threshold=0.8
                    )
                    
                    # 状態異常が検出されなかった場合は画像を削除
                    if not ailment_result:
                        if os.path.exists(save_path):
                            os.remove(save_path)
                        print(f"⚪ {roi_name}_{frame_idx:06d}: 状態異常なし (保存せず)")
                        continue
                    
                    # 状態異常が検出された場合のみテキストファイルを出力
                    text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
                    text_path = win_safe_path(os.path.join(roi_dir, text_filename))
                    
                    with open(text_path, "w", encoding="utf-8") as f:
                        f.write(ailment_result)
                    
                    print(f"🔴 {roi_name}_{frame_idx:06d}: 状態異常 '{ailment_result}' を出力")
                except Exception as e:
                    print(f"⚠ 状態異常処理エラー ({roi_name}): {e}")
                    # エラー時は画像も削除
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    continue

            supplementary_save_count += 1

        return supplementary_save_count