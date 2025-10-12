# image_matcher.py
import os
import cv2
from glob import glob
from config import ROI_DICT

class ImageMatcher:
    def __init__(self):
        pass
    
    def extract_roi(self, frame, roi_name, width, height):
        """フレームからROI領域を抽出"""
        if roi_name not in ROI_DICT:
            return None
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return None
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            return None
        
        roi_img = frame[y:y+h, x:x+w]
        return roi_img if roi_img.size > 0 else None
    
    def match_single_image(self, frame, roi_name, template_path, width, height, threshold=0.8):
        """単一画像とのマッチング"""
        roi_img = self.extract_roi(frame, roi_name, width, height)
        if roi_img is None:
            return False, 0.0
        
        template = cv2.imread(template_path)
        if template is None:
            print(f"⚠ テンプレート読み込み失敗: {template_path}")
            return False, 0.0
        
        max_val = self.calculate_match_score(roi_img, template)
        
        # 閾値ログ出力
        status = "✅" if max_val >= threshold else "❌"
        print(f"  {status} {roi_name} 画像マッチング: {max_val:.3f} (閾値: {threshold})")
        
        return max_val >= threshold, max_val
    
    def match_multiple_images(self, frame, roi_name, template_dir, width, height, threshold=0.8):
        """複数画像とのマッチング（最高スコアを返す）"""
        roi_img = self.extract_roi(frame, roi_name, width, height)
        if roi_img is None:
            return False, 0.0, ""
        
        best_match_score = 0.0
        best_match_file = ""
        
        for img_path in glob(os.path.join(template_dir, "*.png")):
            template = cv2.imread(img_path)
            if template is None:
                continue
            
            max_val = self.calculate_match_score(roi_img, template)
            
            if max_val > best_match_score:
                best_match_score = max_val
                best_match_file = os.path.basename(img_path)
        
        # 閾値ログ出力
        if best_match_score > 0:
            status = "✅" if best_match_score >= threshold else "❌"
            print(f"  {status} {roi_name} 画像マッチング: {best_match_score:.3f} (ファイル: {best_match_file}, 閾値: {threshold})")
        
        return best_match_score >= threshold, best_match_score, best_match_file
    
    def calculate_match_score(self, roi_img, template):
        """マッチングスコア計算"""
        if roi_img.shape[0] < template.shape[0] or roi_img.shape[1] < template.shape[1]:
            # ROIがテンプレートより小さい場合はリサイズ
            roi_img = cv2.resize(roi_img, (template.shape[1], template.shape[0]))
        
        result = cv2.matchTemplate(roi_img, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val
    
    def check_image_presence(self, frame, roi_name, template_path, width, height, threshold=0.8):
        """画像の存在チェック（シンプル版）"""
        return self.match_single_image(frame, roi_name, template_path, width, height, threshold)