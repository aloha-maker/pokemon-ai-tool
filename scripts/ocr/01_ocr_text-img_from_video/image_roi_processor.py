# image_roi_processor.py
import os
from base_roi_processor import BaseROIProcessor

class ImageROIProcessor(BaseROIProcessor):
    def __init__(self, output_dir, image_matcher):
        super().__init__(output_dir)
        self.image_matcher = image_matcher
    
    def process_image_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, expected_text, template_path=None, threshold=0.8):
        """画像ROIの処理（単一画像、閾値チェック付き）"""
        if template_path and os.path.exists(template_path):
            # 閾値チェックあり
            match_result, max_val = self.image_matcher.match_single_image(
                frame, roi_name, template_path, width, height, threshold
            )
            if not match_result:
                print(f"  ⏭️ {roi_name}_{frame_idx:06d}: 閾値未達 ({max_val:.3f} < {threshold}) のためスキップ")
                return False, max_val
            else:
                print(f"  ✅ {roi_name}_{frame_idx:06d}: 閾値達成 ({max_val:.3f} >= {threshold})")
        
        # ROI画像を抽出して保存
        roi_img = self.extract_roi_image(frame, roi_name, width, height)
        if roi_img is None:
            return False, 0.0
        
        success = self.save_roi_data(roi_img, expected_text, roi_name, video_name, frame_idx, short_hash)
        if success:
            print(f"✔ {roi_name}_{frame_idx:06d}: '{expected_text}'")
        
        return success, 1.0
    
    def process_select_image_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, expected_text, template_path, threshold=0.8):
        """select画像ROI処理（複数画像、閾値ログ出力付き）"""
        match_result, max_val, best_match_file = self.image_matcher.match_single_image(
            frame, roi_name, template_path, width, height, threshold
        )
        
        if not match_result:
            print(f"❌ {roi_name}_{frame_idx:06d}: マッチング失敗 (最高スコア: {max_val:.3f}, 閾値: {threshold})")
            return False, max_val
        
        # ROI画像を抽出して保存
        roi_img = self.extract_roi_image(frame, roi_name, width, height)
        if roi_img is None:
            return False, max_val
        
        success = self.save_roi_data(roi_img, expected_text, roi_name, video_name, frame_idx, short_hash)
        if success:
            print(f"✅ {roi_name}_{frame_idx:06d}: '{expected_text}' (マッチング: {max_val:.3f}, ファイル: {best_match_file})")
        
        return success, max_val
    
    def process_win_lose_roi(self, frame, roi_name, video_name, frame_idx, short_hash, width, height, template_dir, threshold=0.8):
        """win_lose ROI処理（閾値ログ出力付き）"""
        match_result, max_val, best_match_file = self.image_matcher.match_multiple_images(
            frame, roi_name, template_dir, width, height, threshold
        )
        
        if not match_result:
            print(f"❌ {roi_name}_{frame_idx:06d}: マッチング失敗 (最高スコア: {max_val:.3f}, 閾値: {threshold})")
            return False, max_val
        
        # ROI画像を抽出
        roi_img = self.extract_roi_image(frame, roi_name, width, height)
        if roi_img is None:
            return False, max_val
        
        # 画像保存
        image_path = self.save_roi_image(roi_img, roi_name, video_name, frame_idx, short_hash)
        if not image_path:
            return False, max_val
        
        # テキスト保存（ファイル名からwin/loseを判定）
        result_text = os.path.splitext(best_match_file)[0]
        self.save_roi_text(roi_name, video_name, frame_idx, short_hash, result_text)
        
        print(f"✅ {roi_name}_{frame_idx:06d}: '{result_text}' (マッチング: {max_val:.3f})")
        return True, max_val