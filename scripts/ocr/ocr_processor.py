import os
import cv2
import re
import pytesseract
from glob import glob
from config import (
    OUTPUT_DIR, HP_ROIS, AILMENT_ROIS, POKEMON_NAME_ROIS,
    ABILITY_NAME_ROIS, POKEMON_NO_ROIS, ROI_DICT, CUSTOM_CONFIG,
    TESSERACT_PATH, STAY_ROIS, SELECT_ROIS, BATTLE_CHOOSE_ROIS, BATTLE_ACT_ROIS,
    STAY_TEXT_IMAGE, START_IMAGE, SELECT_IMAGES_DIR, WIN_LOSE_IMAGES_DIR,
    TERA_ICONS_DIR, TERA_ME_ICONS_DIR, AILMENT_ICONS_DIR
)
from utils import win_safe_path
from aliment_ocv import identify_ailment_from_cropped_image
from tera_ocv import identify_tera_from_cropped_image
from hp_ocv import get_hp_percentage


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
        self.ailment_icons_dir = AILMENT_ICONS_DIR

    # ==========================
    # 名前補正メソッドの追加
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

    # ==========================
    # フェーズ判定（閾値ログ出力追加）
    # ==========================
    def detect_phase(self, frame, phase_manager, width, height):
        """現在のフェーズを判定"""
        # stayフェーズ: stay_textの検出
        if phase_manager.current_phase == "stay":
            match_result, max_val = self._check_image_match_with_log(frame, 'stay_text', STAY_TEXT_IMAGE, width, height)
            if match_result:
                phase_manager.current_phase = "select"
                phase_manager.mark_processed('stay_text')
                print(f"  🔄 フェーズ変更: stay → select (stay_text 閾値: {max_val:.3f})")
        
        # selectフェーズ: startの検出
        elif phase_manager.current_phase == "select":
            match_result, max_val = self._check_image_match_with_log(frame, 'start', START_IMAGE, width, height)
            if match_result:
                phase_manager.current_phase = "battle"
                phase_manager.mark_processed('start')
                phase_manager.battle_sub_phase = "choose"
                print(f"  🔄 フェーズ変更: select → battle.choose (start 閾値: {max_val:.3f})")
        
        # battleフェーズ: サブフェーズ判定
        elif phase_manager.current_phase == "battle":
            # chooseフェーズ: my_pokemon_nameの検出
            if phase_manager.battle_sub_phase == "choose":
                has_text, _, conf = self._extract_roi_text(frame, 'my_pokemon_name', width, height)
                if not has_text:
                    phase_manager.battle_sub_phase = "act"
                    phase_manager.reset_battle_flags()
                    print(f"  🔄 バトルサブフェーズ変更: choose → act (my_pokemon_name OCR信頼度: {conf['max']:.1f})")
            
            # actフェーズ: win_loseの検出でstayに戻る
            elif phase_manager.battle_sub_phase == "act":
                match_result, max_val = self._check_win_lose_with_log(frame, width, height)
                if match_result:
                    phase_manager.current_phase = "stay"
                    print(f"  🔄 フェーズ変更: battle.act → stay (win_lose 閾値: {max_val:.3f})")
        
        return phase_manager

    def _check_image_match_with_log(self, frame, roi_name, template_path, width, height, threshold=0.8):
        """画像マッチングによるROI検出（閾値ログ出力付き）"""
        if roi_name not in ROI_DICT:
            return False, 0.0
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False, 0.0
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, 0.0
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, 0.0
        
        template = cv2.imread(template_path)
        if template is None:
            print(f"⚠ テンプレート読み込み失敗: {template_path}")
            return False, 0.0
        
        # テンプレートマッチング
        result = cv2.matchTemplate(roi_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        
        # 閾値ログ出力
        status = "✅" if max_val >= threshold else "❌"
        print(f"  {status} {roi_name} 画像マッチング: {max_val:.3f} (閾値: {threshold})")
        
        return max_val >= threshold, max_val

    def _check_win_lose_with_log(self, frame, width, height, threshold=0.8):
        """win_lose画像の検出（閾値ログ出力付き）"""
        if 'win_lose' not in ROI_DICT:
            return False, 0.0
        
        value = ROI_DICT['win_lose']
        if not (isinstance(value, list) and len(value) == 4):
            return False, 0.0
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, 0.0
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, 0.0
        
        # win_loseディレクトリ内の全画像とマッチング
        best_match_score = 0.0
        best_match_file = ""
        
        for img_path in glob(os.path.join(WIN_LOSE_IMAGES_DIR, "*.png")):
            template = cv2.imread(img_path)
            if template is None:
                continue
            
            result = cv2.matchTemplate(roi_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_match_score:
                best_match_score = max_val
                best_match_file = os.path.basename(img_path)
        
        # 閾値ログ出力
        if best_match_score > 0:
            status = "✅" if best_match_score >= threshold else "❌"
            print(f"  {status} win_lose 画像マッチング: {best_match_score:.3f} (ファイル: {best_match_file}, 閾値: {threshold})")
        
        return best_match_score >= threshold, best_match_score

    # ==========================
    # フェーズ別ROI処理
    # ==========================
    def process_phase_rois(self, frame, phase_manager, video_name, frame_idx, short_hash, width, height):
        """フェーズに応じたROI処理"""
        processed_count = 0
        
        if phase_manager.current_phase == "stay":
            processed_count = self._process_stay_rois(frame, phase_manager, video_name, frame_idx, short_hash, width, height)
        
        elif phase_manager.current_phase == "select":
            processed_count = self._process_select_rois(frame, phase_manager, video_name, frame_idx, short_hash, width, height)
        
        elif phase_manager.current_phase == "battle":
            if phase_manager.battle_sub_phase == "choose":
                processed_count = self._process_battle_choose_rois(frame, phase_manager, video_name, frame_idx, short_hash, width, height)
            elif phase_manager.battle_sub_phase == "act":
                processed_count = self._process_battle_act_rois(frame, phase_manager, video_name, frame_idx, short_hash, width, height)
        
        return processed_count

    def _process_stay_rois(self, frame, phase_manager, video_name, frame_idx, short_hash, width, height):
        """stayフェーズのROI処理"""
        processed_count = 0
        for roi_name in STAY_ROIS:
            if not phase_manager.should_process_roi(roi_name):
                continue
            
            if roi_name == 'stay_text':
                # 閾値チェック付きで処理
                success = self._process_image_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height, 
                    "対戦相手がみつかりました！", STAY_TEXT_IMAGE, 0.8
                )
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
        
        return processed_count

    def _process_select_rois(self, frame, phase_manager, video_name, frame_idx, short_hash, width, height):
        """selectフェーズのROI処理"""
        processed_count = 0
        for roi_name in SELECT_ROIS:
            if not phase_manager.should_process_roi(roi_name):
                continue
            
            if roi_name == 'select':
                success, max_val = self._process_select_image_roi_with_log(frame, roi_name, video_name, frame_idx, short_hash, width, height, "選出中")
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name == 'opponent_name':
                # OCR ROIは別途閾値チェック
                success, text, conf = self._process_ocr_roi(frame, roi_name, video_name, frame_idx, short_hash, width, height)
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name == 'start':
                # start画像のマッチングチェック
                match_result, max_val = self._check_image_match_with_log(frame, 'start', START_IMAGE, width, height)
                if match_result:
                    success = self._process_image_roi_with_log(frame, roi_name, video_name, frame_idx, short_hash, width, height, "対戦開始")
                    if success:
                        phase_manager.mark_processed(roi_name)
                        processed_count += 1
                else:
                    print(f"  ⏭️ start: 閾値未達 ({max_val:.3f} < 0.8) のためスキップ")
        
        return processed_count

    def _process_select_rois(self, frame, phase_manager, video_name, frame_idx, short_hash, width, height):
        """selectフェーズのROI処理"""
        processed_count = 0
        for roi_name in SELECT_ROIS:
            if not phase_manager.should_process_roi(roi_name):
                continue
            
            if roi_name == 'select':
                success, max_val = self._process_select_image_roi_with_log(frame, roi_name, video_name, frame_idx, short_hash, width, height, "選出中")
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name == 'opponent_name':
                success, text, conf = self._process_ocr_roi(frame, roi_name, video_name, frame_idx, short_hash, width, height)
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name == 'start':
                success, max_val = self._process_image_roi_with_log(frame, roi_name, video_name, frame_idx, short_hash, width, height, "対戦開始")
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
        
        return processed_count

    def _process_battle_choose_rois(self, frame, phase_manager, video_name, frame_idx, short_hash, width, height):
        """battle chooseフェーズのROI処理"""
        processed_count = 0
        for roi_name in BATTLE_CHOOSE_ROIS:
            if not phase_manager.should_process_roi(roi_name):
                continue
            
            if roi_name in ['my_pokemon_name', 'opponent_pokemon_name']:
                success, text, conf = self._process_ocr_roi(frame, roi_name, video_name, frame_idx, short_hash, width, height)
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name in ['my_pokemon_hp', 'opponent_pokemon_hp']:
                success = self._process_hp_roi(frame, roi_name, video_name, frame_idx, short_hash, width, height)
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name in ['my_ailment', 'your_ailment']:
                success = self._process_ailment_roi_with_log(frame, roi_name, video_name, frame_idx, short_hash, width, height)
                if success:
                    phase_manager.mark_processed(roi_name)
                    processed_count += 1
        
        return processed_count

    def _process_battle_act_rois(self, frame, phase_manager, video_name, frame_idx, short_hash, width, height):
        """battle actフェーズのROI処理"""
        processed_count = 0
        for roi_name in BATTLE_ACT_ROIS:
            if roi_name in ['live_comment_row1', 'live_comment_row2', 
                           'my_tokusei_row1', 'my_tokusei_row2',
                           'your_tokusei_row1', 'your_tokusei_row2']:
                success, text, conf = self._process_ocr_roi(frame, roi_name, video_name, frame_idx, short_hash, width, height)
                if success:
                    processed_count += 1
            
            elif roi_name == 'terastal':
                success, max_val = self._process_tera_roi_with_log(frame, roi_name, video_name, frame_idx, short_hash, width, height, TERA_ICONS_DIR)
                if success:
                    processed_count += 1
            
            elif roi_name == 'terastal_me':
                success, max_val = self._process_tera_roi_with_log(frame, roi_name, video_name, frame_idx, short_hash, width, height, TERA_ME_ICONS_DIR, "自分のテラスタル")
                if success:
                    processed_count += 1
            
            elif roi_name == 'win_lose':
                success, max_val = self._process_win_lose_roi_with_log(frame, roi_name, video_name, frame_idx, short_hash, width, height)
                if success:
                    processed_count += 1
        
        return processed_count

    # ==========================
    # ROI処理メソッド（閾値ログ出力追加版）
    # ==========================
    def _process_image_roi_with_log(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, text):
        """画像ROI処理（単一画像、閾値ログ出力付き）"""
        if roi_name not in ROI_DICT:
            return False, 0.0
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False, 0.0
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, 0.0
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, 0.0
        
        # 画像保存
        roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
        save_path = win_safe_path(os.path.join(roi_dir, filename))
        
        if not cv2.imwrite(save_path, roi_img):
            print(f"⚠ 保存失敗: {save_path}")
            return False, 0.0
        
        # テキスト保存
        text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
        text_path = win_safe_path(os.path.join(roi_dir, text_filename))
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        print(f"✔ {roi_name}_{frame_idx:06d}: '{text}'")
        return True, 1.0  # 単純な画像保存の場合は常に成功

    def _process_select_image_roi_with_log(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, text):
        """select画像ROI処理（複数画像、閾値ログ出力付き）"""
        if roi_name not in ROI_DICT:
            return False, 0.0
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False, 0.0
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, 0.0
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, 0.0
        
        best_match_score = 0.0
        best_match_file = ""
        
        # SELECT_IMAGES_DIR内の全画像とマッチング
        for img_path in glob(os.path.join(SELECT_IMAGES_DIR, "*.png")):
            template = cv2.imread(img_path)
            if template is None:
                continue
            
            result = cv2.matchTemplate(roi_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_match_score:
                best_match_score = max_val
                best_match_file = os.path.basename(img_path)
        
        # 閾値判定とログ出力
        threshold = 0.8
        if best_match_score >= threshold:
            # 画像保存
            roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
            os.makedirs(roi_dir, exist_ok=True)
            filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
            save_path = win_safe_path(os.path.join(roi_dir, filename))
            
            if not cv2.imwrite(save_path, roi_img):
                print(f"⚠ 保存失敗: {save_path}")
                return False, best_match_score
            
            # テキスト保存
            text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
            text_path = win_safe_path(os.path.join(roi_dir, text_filename))
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            print(f"✅ {roi_name}_{frame_idx:06d}: '{text}' (マッチング: {best_match_score:.3f}, ファイル: {best_match_file})")
            return True, best_match_score
        else:
            print(f"❌ {roi_name}_{frame_idx:06d}: マッチング失敗 (最高スコア: {best_match_score:.3f}, 閾値: {threshold})")
            return False, best_match_score

    def _process_win_lose_roi_with_log(self, frame, roi_name, video_name, frame_idx, short_hash, width, height):
        """win_lose ROI処理（閾値ログ出力付き）"""
        if roi_name not in ROI_DICT:
            return False, 0.0
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False, 0.0
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, 0.0
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, 0.0
        
        best_match_score = 0.0
        best_match_file = ""
        
        # WIN_LOSE_IMAGES_DIR内の全画像とマッチング
        for img_path in glob(os.path.join(WIN_LOSE_IMAGES_DIR, "*.png")):
            template = cv2.imread(img_path)
            if template is None:
                continue
            
            result = cv2.matchTemplate(roi_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_match_score:
                best_match_score = max_val
                best_match_file = os.path.basename(img_path)
        
        # 閾値判定
        threshold = 0.8
        if best_match_score >= threshold:
            # 画像保存
            roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
            os.makedirs(roi_dir, exist_ok=True)
            filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
            save_path = win_safe_path(os.path.join(roi_dir, filename))
            
            if not cv2.imwrite(save_path, roi_img):
                print(f"⚠ 保存失敗: {save_path}")
                return False, best_match_score
            
            # テキスト保存（ファイル名からwin/loseを判定）
            result_text = os.path.splitext(best_match_file)[0]
            text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
            text_path = win_safe_path(os.path.join(roi_dir, text_filename))
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(result_text)
            
            print(f"✅ {roi_name}_{frame_idx:06d}: '{result_text}' (マッチング: {best_match_score:.3f})")
            return True, best_match_score
        else:
            print(f"❌ {roi_name}_{frame_idx:06d}: マッチング失敗 (最高スコア: {best_match_score:.3f}, 閾値: {threshold})")
            return False, best_match_score

    def _process_ocr_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height):
        """OCR ROI処理"""
        if roi_name not in ROI_DICT:
            return False, "", {"max": 0, "median": 0, "avg": 0}
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False, "", {"max": 0, "median": 0, "avg": 0}
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, "", {"max": 0, "median": 0, "avg": 0}
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, "", {"max": 0, "median": 0, "avg": 0}
        
        return self._extract_and_save_ocr_text(roi_img, roi_name, video_name, frame_idx, short_hash)

    def _process_hp_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height):
        """HP ROI処理"""
        if roi_name not in ROI_DICT:
            return False
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False
        
        # 画像保存
        roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
        save_path = win_safe_path(os.path.join(roi_dir, filename))
        
        if not cv2.imwrite(save_path, roi_img):
            print(f"⚠ 保存失敗: {save_path}")
            return False
        
        # HP割合計算
        try:
            hp_percent = get_hp_percentage(save_path)
            text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
            text_path = win_safe_path(os.path.join(roi_dir, text_filename))
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(f"{hp_percent:.2f}")
            
            print(f"📊 {roi_name}_{frame_idx:06d}: HP {hp_percent:.2f}%")
            return True
        except Exception as e:
            print(f"⚠ HP処理エラー: {e}")
            return False

    def _process_ailment_roi_with_log(self, frame, roi_name, video_name, frame_idx, short_hash, width, height):
        """状態異常ROI処理（閾値ログ出力付き）"""
        if roi_name not in ROI_DICT:
            return False
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False
        
        # 画像保存
        roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
        save_path = win_safe_path(os.path.join(roi_dir, filename))
        
        if not cv2.imwrite(save_path, roi_img):
            print(f"⚠ 保存失敗: {save_path}")
            return False
        
        # 状態異常判別
        try:
            ailment_result = identify_ailment_from_cropped_image(
                save_path, self.ailment_icons_dir, threshold=0.8
            )
            
            if not ailment_result:
                # 状態異常なしの場合は画像を削除
                if os.path.exists(save_path):
                    os.remove(save_path)
                print(f"⚪ {roi_name}_{frame_idx:06d}: 状態異常なし (閾値: 0.8)")
                return False
            
            # 状態異常ありの場合はテキスト保存
            text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
            text_path = win_safe_path(os.path.join(roi_dir, text_filename))
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(ailment_result)
            
            print(f"🔴 {roi_name}_{frame_idx:06d}: 状態異常 '{ailment_result}' (閾値: 0.8)")
            return True
        except Exception as e:
            print(f"⚠ 状態異常処理エラー: {e}")
            if os.path.exists(save_path):
                os.remove(save_path)
            return False

    def _process_tera_roi_with_log(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, icons_dir, default_text=None):
        """テラスタルROI処理（閾値ログ出力付き）"""
        if roi_name not in ROI_DICT:
            return False, 0.0
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False, 0.0
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, 0.0
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, 0.0
        
        # 画像保存
        roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
        save_path = win_safe_path(os.path.join(roi_dir, filename))
        
        if not cv2.imwrite(save_path, roi_img):
            print(f"⚠ 保存失敗: {save_path}")
            return False, 0.0
        
        # テラスタル判別
        try:
            tera_result = identify_tera_from_cropped_image(save_path, icons_dir, threshold=0.8)
            
            if not tera_result and default_text:
                # デフォルトテキストを使用
                tera_result = default_text
            
            if tera_result:
                text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
                text_path = win_safe_path(os.path.join(roi_dir, text_filename))
                with open(text_path, "w", encoding="utf-8") as f:
                    f.write(tera_result)
                
                print(f"💎 {roi_name}_{frame_idx:06d}: テラスタル '{tera_result}' (閾値: 0.8)")
                return True, 1.0
            else:
                print(f"⚪ {roi_name}_{frame_idx:06d}: テラスタルなし (閾値: 0.8)")
                return False, 0.0
        except Exception as e:
            print(f"⚠ テラスタル処理エラー: {e}")
            return False, 0.0

    # ==========================
    # 既存の画像ROI処理メソッド（互換性維持用）
    # ==========================
    def _process_image_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, text, template_path=None, threshold=0.8):
        """画像ROI処理（単一画像、閾値チェック付き）"""
        if roi_name not in ROI_DICT:
            return False
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return False
        
        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False
        
        # テンプレートパスが指定されている場合は閾値チェック
        if template_path and os.path.exists(template_path):
            template = cv2.imread(template_path)
            if template is not None:
                result = cv2.matchTemplate(roi_img, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                if max_val < threshold:
                    print(f"  ⏭️ {roi_name}_{frame_idx:06d}: 閾値未達 ({max_val:.3f} < {threshold}) のためスキップ")
                    return False
                else:
                    print(f"  ✅ {roi_name}_{frame_idx:06d}: 閾値達成 ({max_val:.3f} >= {threshold})")
        
        # 画像保存
        roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
        save_path = win_safe_path(os.path.join(roi_dir, filename))
        
        if not cv2.imwrite(save_path, roi_img):
            print(f"⚠ 保存失敗: {save_path}")
            return False
        
        # テキスト保存
        text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
        text_path = win_safe_path(os.path.join(roi_dir, text_filename))
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        print(f"✔ {roi_name}_{frame_idx:06d}: '{text}'")
        return True
    # ==========================
    # OCR関連メソッド
    # ==========================
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

    def _extract_roi_text(self, frame, roi_name, width, height):
        """ROIからテキストを抽出"""
        if roi_name not in ROI_DICT:
            return False, "", {"max": 0, "median": 0, "avg": 0}

        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False, "", {"max": 0, "median": 0, "avg": 0}

        x, y, w, h = value
        if x + w > width or y + h > height:
            return False, "", {"max": 0, "median": 0, "avg": 0}

        roi_img = frame[y:y+h, x:x+w]
        if roi_img.size == 0:
            return False, "", {"max": 0, "median": 0, "avg": 0}

        text, confidence = self.extract_text_from_image(roi_img, roi_name)
        has_text = bool(text.strip())
        
        # 名前補正を適用
        if has_text:
            text = self.apply_name_correction(text, roi_name)
            
        return has_text, text, confidence

    def _extract_and_save_ocr_text(self, roi_img, roi_name, video_name, frame_idx, short_hash):
        """OCRテキストを抽出して保存"""
        text, confidence = self.extract_text_from_image(roi_img, roi_name)
        if not text:
            return False, "", confidence

        # 名前補正を適用
        text = self.apply_name_correction(text, roi_name)

        # 画像保存
        roi_dir = os.path.join(OUTPUT_DIR, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
        save_path = win_safe_path(os.path.join(roi_dir, filename))

        if not cv2.imwrite(save_path, roi_img):
            print(f"⚠ 保存失敗: {save_path}")
            return False, "", confidence

        # テキスト保存
        text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
        text_path = win_safe_path(os.path.join(roi_dir, text_filename))
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"📝 {roi_name}_{frame_idx:06d}: '{text}' (OCR信頼度: 最大{confidence['max']:.1f}, 平均{confidence['avg']:.1f})")
        return True, text, confidence