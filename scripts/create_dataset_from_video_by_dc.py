import cv2
import json
import os
import sys
import numpy as np
import pytesseract
from PIL import Image
import re

def get_scaled_rois(roi_config, video_width, video_height):
    """
    動画の解像度に合わせてROI座標をスケーリングする。
    """
    ref_width = 1920
    ref_height = 1080
    
    width_scale = video_width / ref_width
    height_scale = video_height / ref_height
    
    scaled_rois = {}
    for key, (x, y, w, h) in roi_config.items():
        if key == "reference_resolution":
            continue
        scaled_rois[key] = [
            int(x * width_scale),
            int(y * height_scale),
            int(w * width_scale),
            int(h * height_scale)
        ]
    return scaled_rois

def preprocess_image_for_ocr(image):
    """
    OCRの精度向上のための画像前処理
    """
    # グレースケール変換
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # コントラスト強調
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 二値化
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # ノイズ除去
    denoised = cv2.medianBlur(binary, 3)
    
    return denoised

def extract_pokemon_name_with_ocr(image, is_japanese=True):
    """
    OCRでポケモン名を抽出（日本語対応）
    """
    try:
        # 画像前処理
        processed_img = preprocess_image_for_ocr(image)
        
        # OCR設定
        lang = 'jpn' if is_japanese else 'eng'
        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンァィゥェォッャュョー0123456789'
        
        # OCR実行
        text = pytesseract.image_to_string(processed_img, lang=lang, config=config)
        
        # テキストクリーニング
        cleaned_text = clean_ocr_text(text.strip())
        
        return cleaned_text if cleaned_text else None
        
    except Exception as e:
        print(f"OCRエラー: {e}")
        return None

def clean_ocr_text(text):
    """
    OCR結果のテキストをクリーニング
    """
    # 空白文字の除去
    text = re.sub(r'\s+', '', text)
    
    # 信頼度の低い短い文字列をフィルタリング
    if len(text) < 2:
        return ""
    
    # 数字のみの結果をフィルタリング
    if text.isdigit():
        return ""
    
    return text

def are_images_different(img1, img2, threshold=1000):
    """
    2つの画像が十分に異なるかどうかを判定する。
    """
    if img1 is None or img2 is None:
        return True
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    return np.sum(diff) > threshold

def manual_verification_gui(image, suggested_text, roi_name, count):
    """
    簡易的な手動確認用GUI（OpenCVベース）
    """
    display_img = cv2.resize(image, (400, 100))
    cv2.putText(display_img, f"OCR: {suggested_text}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(display_img, f"ROI: {roi_name} #{count}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(display_img, "Y:OK, N:Skip, C:Correct", (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    cv2.imshow('OCR Verification', display_img)
    
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord('y') or key == ord('Y'):  # 承認
            cv2.destroyWindow('OCR Verification')
            return suggested_text
        elif key == ord('n') or key == ord('N'):  # スキップ
            cv2.destroyWindow('OCR Verification')
            return None
        elif key == ord('c') or key == ord('C'):  # 手動修正
            corrected_text = input(f"現在のOCR結果: '{suggested_text}'\n修正するテキストを入力: ").strip()
            cv2.destroyWindow('OCR Verification')
            return corrected_text if corrected_text else None
        elif key == 27:  # ESCキー
            cv2.destroyAllWindows()
            return "EXIT"

def main(video_path, roi_json_path, output_dir, file_prefix, enable_ocr=True, manual_verify=True):
    """
    改良版：OCRによる自動化と手動確認のハイブリッド
    """
    if not os.path.exists(video_path):
        print(f"エラー: 動画ファイルが見つかりません: {video_path}")
        return
    if not os.path.exists(roi_json_path):
        print(f"エラー: ROI設定ファイルが見つかりません: {roi_json_path}")
        return
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(roi_json_path, 'r') as f:
        roi_config = json.load(f)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"エラー: 動画ファイルを開けません: {video_path}")
        return

    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    rois = get_scaled_rois(roi_config, video_width, video_height)
    target_rois = {
        "my_pokemon_name": rois["my_pokemon_name"],
        "opponent_pokemon_name": rois["opponent_pokemon_name"]
    }

    print("データセットの生成を開始します...")
    print(f"OCR自動化: {'有効' if enable_ocr else '無効'}")
    print(f"手動確認: {'有効' if manual_verify else '無効'}")
    
    frame_interval = 30
    frame_count = 0
    saved_count = 0
    last_images = {"my_pokemon_name": None, "opponent_pokemon_name": None}
    ocr_cache = {}  # 同じ画像のOCR結果をキャッシュ

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            for roi_name, (x, y, w, h) in target_rois.items():
                cropped_img = frame[y:y+h, x:x+w]
                
                if are_images_different(cropped_img, last_images[roi_name]):
                    img_hash = str(cv2.mean(cropped_img)[0])  # 簡易ハッシュ
                    
                    # OCRによるテキスト抽出
                    detected_text = None
                    if enable_ocr:
                        if img_hash in ocr_cache:
                            detected_text = ocr_cache[img_hash]
                        else:
                            detected_text = extract_pokemon_name_with_ocr(cropped_img, is_japanese=True)
                            ocr_cache[img_hash] = detected_text
                    
                    # 手動確認または自動保存
                    final_text = None
                    if detected_text and manual_verify:
                        final_text = manual_verification_gui(cropped_img, detected_text, roi_name, saved_count)
                        if final_text == "EXIT":
                            print("処理を中断しました")
                            cap.release()
                            cv2.destroyAllWindows()
                            return
                    elif detected_text:
                        final_text = detected_text
                    
                    # 保存
                    if final_text:
                        img_filename = f"{file_prefix}.exp.{saved_count}.png"
                        txt_filename = f"{file_prefix}.exp.{saved_count}.gt.txt"
                        img_path = os.path.join(output_dir, img_filename)
                        txt_path = os.path.join(output_dir, txt_filename)
                        
                        cv2.imwrite(img_path, cropped_img)
                        with open(txt_path, 'w', encoding='utf-8') as f:
                            f.write(final_text)
                        
                        print(f"  -> 保存しました: {img_filename} -> '{final_text}'")
                        saved_count += 1
                    
                    last_images[roi_name] = cropped_img.copy()

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n処理が完了しました。合計 {saved_count} 個の画像を生成しました。")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("使用法: python create_dataset_auto.py <video_path> <roi_json_path> <output_dir> <file_prefix> [--no-ocr] [--auto-save]")
        print("  --no-ocr:     OCRを無効化（完全手動モード）")
        print("  --auto-save:  手動確認をスキップ（OCR結果を自動保存）")
        sys.exit(1)
    
    # オプション解析
    args = sys.argv[1:]
    video_path = args[0]
    roi_json_path = args[1]
    output_dir = args[2]
    file_prefix = args[3]
    
    enable_ocr = "--no-ocr" not in args
    manual_verify = "--auto-save" not in args
    
    main(video_path, roi_json_path, output_dir, file_prefix, enable_ocr, manual_verify)