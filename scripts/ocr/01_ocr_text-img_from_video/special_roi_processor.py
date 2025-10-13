# special_roi_processor.py
import os
from base_roi_processor import BaseROIProcessor
from hp_ocv import get_hp_percentage
from aliment_ocv import identify_ailment_from_cropped_image
from tera_ocv import identify_tera_from_cropped_image
from config import AILMENT_ICONS_DIR, TERA_ICONS_DIR, TERA_ME_ICONS_DIR

class SpecialROIProcessor(BaseROIProcessor):
    def __init__(self, output_dir):
        super().__init__(output_dir)
        self.ailment_icons_dir = AILMENT_ICONS_DIR
    
    def process_hp_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height):
        """HP ROIの処理"""
        roi_img = self.extract_roi_image(frame, roi_name, width, height)
        if roi_img is None:
            return False
        
        # 画像保存
        image_path = self.save_roi_image(roi_img, roi_name, video_name, frame_idx, short_hash)
        if not image_path:
            return False
        
        # HP割合計算
        try:
            hp_percent = get_hp_percentage(image_path)
            self.save_roi_text(roi_name, video_name, frame_idx, short_hash, f"{hp_percent:.2f}")
            
            print(f"📊 {roi_name}_{frame_idx:06d}: HP {hp_percent:.2f}%")
            return True
        except Exception as e:
            print(f"⚠ HP処理エラー: {e}")
            return False
    
    def process_ailment_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, threshold=0.8):
        """状態異常ROI処理（閾値ログ出力付き）"""
        roi_img = self.extract_roi_image(frame, roi_name, width, height)
        if roi_img is None:
            return False
        
        # 画像保存
        image_path = self.save_roi_image(roi_img, roi_name, video_name, frame_idx, short_hash)
        if not image_path:
            return False
        
        # 状態異常判別
        try:
            ailment_result = identify_ailment_from_cropped_image(
                image_path, self.ailment_icons_dir, threshold=threshold
            )
            
            if not ailment_result:
                # 状態異常なしの場合は画像を削除
                if os.path.exists(image_path):
                    os.remove(image_path)
                print(f"⚪ {roi_name}_{frame_idx:06d}: 状態異常なし (閾値: {threshold})")
                return False
            
            # 状態異常ありの場合はテキスト保存
            self.save_roi_text(roi_name, video_name, frame_idx, short_hash, ailment_result)
            
            print(f"🔴 {roi_name}_{frame_idx:06d}: 状態異常 '{ailment_result}' (閾値: {threshold})")
            return True
        except Exception as e:
            print(f"⚠ 状態異常処理エラー: {e}")
            if os.path.exists(image_path):
                os.remove(image_path)
            return False
        
    def process_tera_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, icons_dir, default_text=None, threshold=0.8):
        """テラスタルROI処理（マッチング失敗時は画像保存しない）"""
        roi_img = self.extract_roi_image(frame, roi_name, width, height)
        if roi_img is None:
            return False, 0.0
        
        # テラスタル判別
        try:
            tera_result = identify_tera_from_cropped_image(roi_img, icons_dir, threshold=threshold)
            
            if not tera_result and default_text:
                # デフォルトテキストを使用
                tera_result = default_text
            
            if tera_result:
                # マッチング成功時のみ画像とテキストを保存
                image_path = self.save_roi_image(roi_img, roi_name, video_name, frame_idx, short_hash)
                if image_path:
                    self.save_roi_text(roi_name, video_name, frame_idx, short_hash, tera_result)
                    print(f"💎 {roi_name}_{frame_idx:06d}: テラスタル '{tera_result}' (閾値: {threshold})")
                    return True, 1.0
                else:
                    return False, 0.0
            else:
                # マッチング失敗時は何も保存しない
                print(f"⚪ {roi_name}_{frame_idx:06d}: テラスタルなし (閾値: {threshold})")
                return False, 0.0
                
        except Exception as e:
            print(f"⚠ テラスタル処理エラー: {e}")
            return False, 0.0