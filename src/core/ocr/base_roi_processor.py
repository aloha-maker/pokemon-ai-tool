# base_roi_processor.py
import os
import cv2
from .utils import win_safe_path
from .config import OUTPUT_DIR,ROI_DICT

class BaseROIProcessor:
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = output_dir
    
    def extract_roi_image(self, frame, roi_name, width, height):
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
    
    def save_roi_image(self, roi_img, roi_name, video_name, frame_idx, short_hash):
        """ROI画像を保存"""
        roi_dir = os.path.join(self.output_dir, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.png"
        save_path = win_safe_path(os.path.join(roi_dir, filename))
        
        if not cv2.imwrite(save_path, roi_img):
            print(f"⚠ 保存失敗: {save_path}")
            return None
        
        return save_path
    
    def save_roi_text(self, roi_name, video_name, frame_idx, short_hash, text):
        """ROIテキストを保存"""
        roi_dir = os.path.join(self.output_dir, video_name, roi_name)
        os.makedirs(roi_dir, exist_ok=True)
        text_filename = f"{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt"
        text_path = win_safe_path(os.path.join(roi_dir, text_filename))
        
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        return text_path
    
    def save_roi_data(self, roi_img, text, roi_name, video_name, frame_idx, short_hash):
        """ROIデータを保存（画像＋テキスト）"""
        image_path = self.save_roi_image(roi_img, roi_name, video_name, frame_idx, short_hash)
        if not image_path:
            return False
        
        self.save_roi_text(roi_name, video_name, frame_idx, short_hash, text)
        return True
    
    def validate_roi(self, frame, roi_name, width, height):
        """ROIの有効性をチェック"""
        from config import ROI_DICT
        
        if roi_name not in ROI_DICT:
            return False
        
        value = ROI_DICT[roi_name]
        if not (isinstance(value, list) and len(value) == 4):
            return False
        
        x, y, w, h = value
        return not (x + w > width or y + h > height)