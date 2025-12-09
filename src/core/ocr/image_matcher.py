# image_matcher.py
import os
import cv2
from glob import glob
from .config import ROI_DICT

class ImageMatcher:
    def __init__(self):
        pass
    
    def extract_roi(self, frame, roi_name, width, height):
        """フレームからROI領域を抽出"""
        if roi_name not in ROI_DICT:
            print(f"⚠ ROI '{roi_name}' がROI_DICTに存在しません")
            return None
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            print(f"⚠ ROI '{roi_name}' の値が不正です: {value}")
            return None
        
        x, y, w, h = value
        if x + w > width or y + h > height:
            print(f"⚠ ROI '{roi_name}' がフレーム範囲外です: {x},{y},{w},{h} (フレーム: {width}x{height})")
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
        
        return max_val >= threshold, max_val
    
    def match_multiple_images(self, frame, roi_name, template_dir, width, height, threshold=0.8):
        """複数画像とのマッチング（最高スコアを返す）"""
        roi_img = self.extract_roi(frame, roi_name, width, height)
        if roi_img is None:
            return False, 0.0, ""
        
        best_match_score = 0.0
        best_match_file = ""
        all_scores = []  # すべてのスコアを記録
        
        template_files = list(glob(os.path.join(template_dir, "*.png")))
        if not template_files:
            print(f"⚠ テンプレートファイルが見つかりません: {template_dir}")
            return False, 0.0, ""
        
        print(f"  🔍 {roi_name}: {len(template_files)}個のテンプレートとマッチング")
        
        for img_path in template_files:
            template = cv2.imread(img_path)
            if template is None:
                continue
            
            max_val = self.calculate_match_score(roi_img, template)
            all_scores.append((os.path.basename(img_path), max_val))
            
            if max_val > best_match_score:
                best_match_score = max_val
                best_match_file = os.path.basename(img_path)
        
        # 詳細なスコア情報をログ出力
        if all_scores:
            # スコアでソート
            all_scores.sort(key=lambda x: x[1], reverse=True)
            print(f"  📊 {roi_name} マッチングスコア詳細:")
            for i, (file, score) in enumerate(all_scores[:5]):  # 上位5件を表示
                indicator = "🏆" if i == 0 else "  "
                print(f"    {indicator} {file}: {score:.3f}")
            
            if len(all_scores) > 5:
                print(f"    ... 他{len(all_scores) - 5}件")
        
        # 閾値ログ出力
        # if best_match_score > 0:
        #     status = "✅" if best_match_score >= threshold else "❌"
        #     print(f"  {status} {roi_name} 最高マッチング: {best_match_score:.3f} (ファイル: {best_match_file}, 閾値: {threshold})")
        # else:
        #     print(f"  ❌ {roi_name}: 有効なマッチングが見つかりませんでした")
        
        return best_match_score >= threshold, best_match_score, best_match_file
    
    def calculate_match_score(self, roi_img, template):
        """マッチングスコア計算"""
        if roi_img.shape[0] < template.shape[0] or roi_img.shape[1] < template.shape[1]:
            # ROIがテンプレートより小さい場合はリサイズ
            try:
                roi_img = cv2.resize(roi_img, (template.shape[1], template.shape[0]))
            except Exception as e:
                print(f"⚠ ROIリサイズエラー: {e}")
                return 0.0
        
        try:
            result = cv2.matchTemplate(roi_img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            return max_val
        except Exception as e:
            print(f"⚠ マッチング計算エラー: {e}")
            return 0.0
    
    def check_image_presence(self, frame, roi_name, template_path, width, height, threshold=0.8):
        """画像の存在チェック（シンプル版）"""
        return self.match_single_image(frame, roi_name, template_path, width, height, threshold)