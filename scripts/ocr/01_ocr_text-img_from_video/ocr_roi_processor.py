# ocr_roi_processor.py
import os
import cv2
import re
import pytesseract
from base_roi_processor import BaseROIProcessor
from config import CUSTOM_CONFIG, POKEMON_NAME_ROIS, ABILITY_NAME_ROIS, POKEMON_NO_ROIS

class OCRROIProcessor(BaseROIProcessor):
    def __init__(self, output_dir, pokemon_corrector, ability_corrector):
        super().__init__(output_dir)
        self.pokemon_corrector = pokemon_corrector
        self.ability_corrector = ability_corrector
        
        # 直前のポケモン名を保持
        self.last_my_pokemon_name = ""
        self.last_opponent_pokemon_name = ""
    
    def process_ocr_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height):
        """OCR ROIの処理"""
        roi_img = self.extract_roi_image(frame, roi_name, width, height)
        if roi_img is None:
            return False, "", {"max": 0, "median": 0, "avg": 0}
        
        return self._extract_and_save_ocr_text(roi_img, roi_name, video_name, frame_idx, short_hash)
    
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

            # 確信度が0以上のテキストのみ抽出
            text_parts = []
            confidences = []
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0 and data['text'][i].strip():
                    text_parts.append(data['text'][i].strip())
                    confidences.append(float(conf))

            text = " ".join(text_parts)
            text = self.clean_text(text)

            if not confidences:
                return text, {"max": 0, "median": 0, "avg": 0}

            return text, {
                "max": max(confidences),
                "median": sorted(confidences)[len(confidences) // 2],
                "avg": sum(confidences) / len(confidences)
            }
        except Exception as e:
            print(f"⚠ OCRエラー: {e}")
            return "", {"max": 0, "median": 0, "avg": 0}
    
    @staticmethod
    def preprocess_image(image):
        """OCR前のノイズ除去・二値化"""
        if image is None or image.size == 0:
            return None

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        denoised = cv2.medianBlur(gray, 3)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    
    @staticmethod
    def clean_text(text):
        """空白削除・記号統一・誤字修正"""
        if not text:
            return ""
            
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
    
    def _extract_and_save_ocr_text(self, roi_img, roi_name, video_name, frame_idx, short_hash):
        """OCRテキストを抽出して保存"""
        text, confidence = self.extract_text_from_image(roi_img, roi_name)
        if not text:
            return False, "", confidence

        # 名前補正を適用
        text = self.apply_name_correction(text, roi_name)

        # 画像保存
        image_path = self.save_roi_image(roi_img, roi_name, video_name, frame_idx, short_hash)
        if not image_path:
            return False, "", confidence

        # テキスト保存
        self.save_roi_text(roi_name, video_name, frame_idx, short_hash, text)

        print(f"📝 {roi_name}_{frame_idx:06d}: '{text}' (OCR信頼度: 最大{confidence['max']:.1f}, 平均{confidence['avg']:.1f})")
        return True, text, confidence