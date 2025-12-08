import os
import pytesseract
from .phase_manager import PhaseManager
from .image_matcher import ImageMatcher
from .ocr_roi_processor import OCRROIProcessor
from .image_roi_processor import ImageROIProcessor
from .special_roi_processor import SpecialROIProcessor
from .config import (
    OUTPUT_DIR, HP_ROIS, AILMENT_ROIS, POKEMON_NAME_ROIS,
    ABILITY_NAME_ROIS, POKEMON_NO_ROIS, ROI_DICT, CUSTOM_CONFIG,
    SELECT_ROIS, BATTLE_CHOOSE_ROIS, BATTLE_ACT_ROIS,
    START_IMAGE, SELECT_IMAGES_PATH, WIN_LOSE_IMAGES_DIR,
    TERA_ICONS_DIR, TERA_ME_ICONS_DIR, AILMENT_ICONS_DIR
)

from flask import current_app

class OCRProcessor:
    def __init__(self, pokemon_corrector, ability_corrector, tesseract_path):
        self.pokemon_corrector = pokemon_corrector
        self.ability_corrector = ability_corrector
        
        # 各プロセッサーの初期化
        self.phase_manager = PhaseManager()
        self.image_matcher = ImageMatcher()
        self.ocr_processor = OCRROIProcessor(OUTPUT_DIR, pokemon_corrector, ability_corrector)
        self.image_processor = ImageROIProcessor(OUTPUT_DIR, self.image_matcher)
        self.special_processor = SpecialROIProcessor(OUTPUT_DIR)
        
        # テッセラクト設定 (引数から取得)
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        self.current_battle_id = ""
        self.result = "unknown"

    def detect_phase(self, frame, width, height):
        """現在のフェーズを判定"""
        # stayフェーズ: select ROIの検出
        self.phase_manager.stop_flag = False
        self.phase_manager.return_flag = False
        if self.phase_manager.current_phase == "stay":
            match_result, max_val = self.image_matcher.match_single_image(
                frame, 'select', SELECT_IMAGES_PATH, width, height
            )
            if match_result:
                self.phase_manager.set_phase("select")
                self.phase_manager.stop_flag = True
                self.phase_manager.return_flag = True
                print(f"  🔄 フェーズ変更: stay → select (select ROI 閾値: {max_val:.3f})")
        
        # selectフェーズ: my_pokemon_nameの有効読み取りでbattle.chooseへ
        elif self.phase_manager.current_phase == "select":
            match_result, max_val = self.image_matcher.match_single_image(
                frame, 'start', START_IMAGE, width, height
            )
            if match_result:
                self.phase_manager.set_phase("battle", "act")
                self.phase_manager.return_flag = True
                print(f"  🔄 フェーズ変更: select → battle.act (select ROI 閾値: {max_val:.3f})")
        
        # battleフェーズ: サブフェーズ判定
        elif self.phase_manager.current_phase == "battle":

            # chooseフェーズ: my_pokemon_nameの検出
            if self.phase_manager.battle_sub_phase == "choose":
                # TODO：if has_text and text and text.strip()がTRUEの場合は何もしない
                print(f"  🔍 battle.chooseフェーズ: 自分のポケモン名を検出中...")
                has_text, text, conf = self.ocr_processor.process_ocr_roi(
                    frame, 'my_pokemon_name', "", 0, "", width, height
                )
                
                if has_text and text and text.strip():
                    print(f"  ⏭️ battle.chooseフェーズ継続: ポケモン名検出中")
                else:
                    self.phase_manager.set_phase("battle", "act")
                    self.phase_manager.reset_battle_flags()
                    self.phase_manager.return_flag = True
                    print(f"  🔄 バトルサブフェーズ変更: choose → act (my_pokemon_name OCRテキストなし)")
            
            # actフェーズ: win_loseの検出でstayに戻る または 新しいポケモンでchooseに戻る
            elif self.phase_manager.battle_sub_phase == "act":
                # win_loseの検出でstayに戻る
                print(f"  🔍 battle.actフェーズ: 勝敗画面を検出中...")
                match_result, max_val, best_file = self.image_matcher.match_multiple_images(
                    frame, 'win_lose', WIN_LOSE_IMAGES_DIR, width, height
                )
                # ファイル名からwin/loseを判定
                result_text = os.path.splitext(best_file)[0]
                self.phase_manager.return_flag = True
                if match_result:
                    self.phase_manager.set_phase("stay")
                    self.phase_manager.stop_flag = True
                    self.result = result_text
                    print(f"  🔄 フェーズ変更: battle.act → stay (win_lose 閾値: {max_val:.3f}, 結果: {result_text})")

                # chooseフェーズ: my_pokemon_nameの検出
                has_text, text, conf = self.ocr_processor.process_ocr_roi(
                    frame, 'my_pokemon_name', "", 0, "", width, height
                )
                if has_text and text and text.strip():
                    self.phase_manager.set_phase("battle", "choose")
                    self.phase_manager.reset_battle_flags()
                    self.phase_manager.stop_flag = True 
                    print(f"  🔄 フェーズ変更: act → choose (ポケモン名: '{text}', 信頼度: 最大{conf['max']:.1f})")
        return self.phase_manager
    
    def process_phase_rois(self, frame, video_name, frame_idx, short_hash, width, height):
        """フェーズ別ROI処理のルーティング"""
        # 新しいフレームの処理の開始時に前回の結果をクリア
        self.ocr_processor.clear_results()

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
        """stayフェーズの処理（STAY_ROIS削除に伴い空実装）"""
        # stayフェーズでは特別なROI処理は行わない
        # select ROIの検出はdetect_phaseで行う
        return 0
        
    def _process_select_rois(self, frame, video_name, frame_idx, short_hash, width, height):
        """selectフェーズの処理（start処理を削除）"""
        processed_count = 0
        for roi_name in SELECT_ROIS:
            if not self.phase_manager.should_process_roi(roi_name):
                continue
            
            if roi_name == 'select':
                # select ROIは「対戦相手が見つかりました！」テキストで保存
                success, max_val = self.image_processor.process_image_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height,
                    "対戦相手が見つかりました！", SELECT_IMAGES_PATH, 0.8
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
                else:
                    print(f"  ⏭️ select ROI処理スキップ: マッチングスコア不足 ({max_val:.3f} < 0.8)")
            
            elif roi_name in ['opponent_name', 'battle_id']:
                success, text, conf = self.ocr_processor.process_ocr_roi(
                    frame, roi_name, video_name, frame_idx, short_hash, width, height
                )
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
                    
                    # battle_idが読み取れた場合は設定
                    if roi_name == 'battle_id' and text:
                        self.current_battle_id = text
                        self.ocr_processor.set_battle_id(text)  # OCRプロセッサーに設定
                        print(f"🎯 バトルID設定: {text}")
        
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
                # 成功した場合のみ処理済みとしてマーク（閾値未満の場合はsuccess=False）
                if success:
                    self.phase_manager.mark_processed(roi_name)
                    processed_count += 1
                else:
                    print(f"  ⏭️ {roi_name} 処理スキップ: 類似度閾値未達")
            
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
                    TERA_ICONS_DIR, None, 0.7
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
        
        return processed_count
    
    def get_current_phase_info(self):
        """現在のフェーズ情報を取得"""
        return self.phase_manager.get_current_phase_info()
    
    def reset_phase(self):
        """フェーズをリセット"""
        self.phase_manager.set_phase("stay")
    
    def reset_for_new_video(self):
        """新しい動画処理用に状態をリセット"""
        self.reset_phase()
    
    def set_pokemon_corrector(self, new_corrector):
        """ポケモン名補正器を再設定"""
        self.pokemon_corrector = new_corrector
        self.ocr_processor.pokemon_corrector = new_corrector
        print("✅ pokemon_corrector を再設定しました。")