# ocr_processor.py（リファクタリング後）
import os
import pytesseract
from phase_manager import PhaseManager
from image_matcher import ImageMatcher
from ocr_roi_processor import OCRROIProcessor
from image_roi_processor import ImageROIProcessor
from special_roi_processor import SpecialROIProcessor
from config import (
    OUTPUT_DIR, HP_ROIS, AILMENT_ROIS, POKEMON_NAME_ROIS,
    ABILITY_NAME_ROIS, POKEMON_NO_ROIS, ROI_DICT, CUSTOM_CONFIG,
    TESSERACT_PATH, STAY_ROIS, SELECT_ROIS, BATTLE_CHOOSE_ROIS, BATTLE_ACT_ROIS,
    STAY_TEXT_IMAGE, START_IMAGE, SELECT_IMAGES_DIR, WIN_LOSE_IMAGES_DIR,
    TERA_ICONS_DIR, TERA_ME_ICONS_DIR, AILMENT_ICONS_DIR
)

class OCRProcessor:
    def __init__(self, pokemon_corrector, ability_corrector):
        self.pokemon_corrector = pokemon_corrector
        self.ability_corrector = ability_corrector
        
        # 各プロセッサーの初期化
        self.phase_manager = PhaseManager()
        self.image_matcher = ImageMatcher()
        self.ocr_processor = OCRROIProcessor(OUTPUT_DIR, pokemon_corrector, ability_corrector)
        self.image_processor = ImageROIProcessor(OUTPUT_DIR, self.image_matcher)
        self.special_processor = SpecialROIProcessor(OUTPUT_DIR)
        
        # テッセラクト設定
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        # 直前のポケモン名を保持（act→choose遷移用）
        self.last_my_pokemon_name = ""
        self.last_opponent_pokemon_name = ""
    
    def detect_phase(self, frame, width, height):
        """現在のフェーズを判定（act→choose遷移追加）"""
        # stayフェーズ: stay_textの検出
        if self.phase_manager.current_phase == "stay":
            match_result, max_val = self.image_matcher.match_single_image(
                frame, 'stay_text', STAY_TEXT_IMAGE, width, height
            )
            if match_result:
                self.phase_manager.set_phase("select")
                print(f"  🔄 フェーズ変更: stay → select (stay_text 閾値: {max_val:.3f})")
        
        # selectフェーズ: startの検出
        elif self.phase_manager.current_phase == "select":
            match_result, max_val = self.image_matcher.match_single_image(
                frame, 'start', START_IMAGE, width, height
            )
            if match_result:
                self.phase_manager.set_phase("battle", "choose")
                print(f"  🔄 フェーズ変更: select → battle.choose (start 閾値: {max_val:.3f})")
        
        # battleフェーズ: サブフェーズ判定
        elif self.phase_manager.current_phase == "battle":
            # chooseフェーズ: my_pokemon_nameの検出
            if self.phase_manager.battle_sub_phase == "choose":
                has_text, text, conf = self.ocr_processor.process_ocr_roi(
                    frame, 'my_pokemon_name', "", 0, "", width, height
                )
                if has_text and text:
                    # 新しいポケモン名を記録
                    self.last_my_pokemon_name = text
                
                if not has_text:
                    self.phase_manager.set_phase("battle", "act")
                    self.phase_manager.reset_battle_flags()
                    print(f"  🔄 バトルサブフェーズ変更: choose → act (my_pokemon_name OCR信頼度: {conf['max']:.1f})")
            
            # actフェーズ: win_loseの検出でstayに戻る または 新しいポケモンでchooseに戻る
            elif self.phase_manager.battle_sub_phase == "act":
                # win_loseの検出でstayに戻る（既存）
                match_result, max_val, _ = self.image_matcher.match_multiple_images(
                    frame, 'win_lose', WIN_LOSE_IMAGES_DIR, width, height
                )
                if match_result:
                    self.phase_manager.set_phase("stay")
                    print(f"  🔄 フェーズ変更: battle.act → stay (win_lose 閾値: {max_val:.3f})")
                
                # 新しい条件: 新しいポケモンが登場したらchooseに戻る（追加）
                elif self._is_new_pokemon_appeared(frame, width, height):
                    self.phase_manager.set_phase("battle", "choose")
                    self.phase_manager.reset_battle_flags()
                    print(f"  🔄 バトルサブフェーズ変更: act → choose (新しいポケモン登場)")
        
        return self.phase_manager
    
    def _is_new_pokemon_appeared(self, frame, width, height):
        """新しいポケモンが登場したか判定"""
        has_text, new_name, conf = self.ocr_processor.process_ocr_roi(
            frame, 'my_pokemon_name', "", 0, "", width, height
        )
        
        if has_text and new_name and new_name != self.last_my_pokemon_name:
            print(f"  🆕 新しいポケモン登場: {self.last_my_pokemon_name} → {new_name}")
            self.last_my_pokemon_name = new_name
            return True
        
        return False
    
    def process_phase_rois(self, frame, video_name, frame_idx, short_hash, width, height):
        """フェーズ別ROI処理のルーティング"""
        processed_count = 0
        
        if self.phase_manager.current_phase == "stay":
            processed_count = self._process_stay_rois(frame, video_name, frame_idx, short_hash, width, height)
        elif self.phase_manager.current_phase == "select":
            processed_count = self._process_select_rois(frame, video_name, frame_idx, short_hash, width, height)
        elif self.phase_manager.current_phase == "battle":
            if self.phase_manager.battle_sub_phase == "choose":
                processed_count = self._process_battle_choose_rois(frame, video_name, frame_idx, short_hash, width, height)
            elif self.phase_manager.battle_sub_phase == "act":
                processed_count = self._process_battle_act_rois(frame, video_name, frame_idx, short_hash, width, height)
        
        return processed_count
    
    def _process_stay_rois(self, frame, video_name, frame_idx, short_hash, width, height):
        """stayフェーズの処理"""
        processed_count = 0
        for roi_name in STAY_ROIS:
            if not self.phase_manager.should_process_roi(roi_name):
                continue
            
            if roi_name == 'stay_text':
                success, _ = self.image_processor.process_image_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height,
                    "対戦相手がみつかりました！", STAY_TEXT_IMAGE, 0.8
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
        
        return processed_count
    
    def _process_select_rois(self, frame, video_name, frame_idx, short_hash, width, height):
        """selectフェーズの処理"""
        processed_count = 0
        for roi_name in SELECT_ROIS:
            if not self.phase_manager.should_process_roi(roi_name):
                continue
            
            if roi_name == 'select':
                success, _ = self.image_processor.process_select_image_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height,
                    "選出中", SELECT_IMAGES_DIR, 0.8
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name == 'opponent_name':
                success, text, conf = self.ocr_processor.process_ocr_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name == 'start':
                success, _ = self.image_processor.process_image_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height,
                    "対戦開始", START_IMAGE, 0.8
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
        
        return processed_count
    
    def _process_battle_choose_rois(self, frame, video_name, frame_idx, short_hash, width, height):
        """battle chooseフェーズの処理"""
        processed_count = 0
        for roi_name in BATTLE_CHOOSE_ROIS:
            if not self.phase_manager.should_process_roi(roi_name):
                continue
            
            if roi_name in ['my_pokemon_name', 'opponent_pokemon_name']:
                success, text, conf = self.ocr_processor.process_ocr_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name in ['my_pokemon_hp', 'opponent_pokemon_hp']:
                success = self.special_processor.process_hp_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
            
            elif roi_name in ['my_ailment', 'your_ailment']:
                success = self.special_processor.process_ailment_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height, 0.8
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
        
        return processed_count
    
    def _process_battle_act_rois(self, frame, video_name, frame_idx, short_hash, width, height):
        """battle actフェーズの処理"""
        processed_count = 0
        for roi_name in BATTLE_ACT_ROIS:
            if roi_name in ['live_comment_row1', 'live_comment_row2', 
                           'my_tokusei_row1', 'my_tokusei_row2',
                           'your_tokusei_row1', 'your_tokusei_row2']:
                success, text, conf = self.ocr_processor.process_ocr_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height
                )
                if success:
                    processed_count += 1
            
            elif roi_name == 'terastal':
                success, _ = self.special_processor.process_tera_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height,
                    TERA_ICONS_DIR, None, 0.8
                )
                if success:
                    processed_count += 1
            
            elif roi_name == 'terastal_me':
                success, _ = self.special_processor.process_tera_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height,
                    TERA_ME_ICONS_DIR, "自分のテラスタル", 0.8
                )
                if success:
                    processed_count += 1
            
            elif roi_name == 'win_lose':
                success, _ = self.image_processor.process_win_lose_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height,
                    WIN_LOSE_IMAGES_DIR, 0.8
                )
                if success:
                    processed_count += 1
        
        return processed_count
    
    def get_current_phase_info(self):
        """現在のフェーズ情報を取得"""
        return self.phase_manager.get_current_phase_info()
    
    def reset_phase(self):
        """フェーズをリセット"""
        self.phase_manager.set_phase("stay")
        self.last_my_pokemon_name = ""
        self.last_opponent_pokemon_name = ""
    
    def reset_for_new_video(self):
        """新しい動画処理用に状態をリセット"""
        self.reset_phase()
        self.ocr_processor.last_my_pokemon_name = ""
        self.ocr_processor.last_opponent_pokemon_name = ""