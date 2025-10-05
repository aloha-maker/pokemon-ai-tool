
import cv2
import sys
import os
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
# 相対パスでモジュールをインポートするためにパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.ocr import GameStateParser

def draw_text_pil(image, text, position, font_path="C:/Windows/Fonts/YuGothM.ttc", font_size=20, color=(255, 0, 0)):
    """Pillowを使って画像に日本語テキストを描画する。"""
    pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"警告: フォントファイル '{font_path}' が見つかりません。デフォルトフォントを使用します。")
        font = ImageFont.load_default()
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def main(video_path):
    """
    動画ファイルから静止かつUIが表示された場面を検出し、OCR結果を可視化する。
    """
    output_dir = "verification_results"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    max_samples = 10  # 最大10シーンまで検証
    saved_samples = 0

    if not os.path.exists(video_path):
        print(f"エラー: 動画ファイルが見つかりません: {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"エラー: 動画ファイルを開けません: {video_path}")
        return

    # GameStateParserとテンプレートを初期化
    parser = GameStateParser(
        roi_config_path='instance/roi_config.json',
        pokemon_master_path='data/master_data/pokemons.csv'
    )
    templates = {"my_status": cv2.imread(".img/my_status.png", cv2.IMREAD_GRAYSCALE)}
    if templates["my_status"] is None:
        print("警告: テンプレート画像 .img/my_status.png の読み込みに失敗しました。")
        # テンプレートがなくても処理を続けるか、ここで終了するか選択
        # return 

    prev_frame_gray = None
    MOTION_THRESHOLD = 15000
    TEMPLATE_MATCH_THRESHOLD = 0.8
    ocr_triggered_on_static_frame = False

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Starting verification... Total frames: {total_frames}. Will capture up to {max_samples} static scenes with UI.")

    while cap.isOpened() and saved_samples < max_samples:
        ret, frame = cap.read()
        if not ret:
            break

        current_frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # --- テンプレートマッチング ---
        ui_found = False
        if templates.get("my_status") is not None:
            res = cv2.matchTemplate(frame_gray, templates["my_status"], cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val >= TEMPLATE_MATCH_THRESHOLD:
                ui_found = True

        # --- フレーム差分計算 ---
        blurred_gray = cv2.GaussianBlur(frame_gray, (5, 5), 0)
        motion_detected = False
        if prev_frame_gray is not None:
            frame_delta = cv2.absdiff(prev_frame_gray, blurred_gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            motion_amount = cv2.countNonZero(thresh)
            if motion_amount > MOTION_THRESHOLD:
                motion_detected = True
                if ocr_triggered_on_static_frame:
                    ocr_triggered_on_static_frame = False
        prev_frame_gray = blurred_gray

        # --- OCR実行判定 ---
        if ui_found and not motion_detected and not ocr_triggered_on_static_frame:
            print(f"--- Static scene with UI found at frame {current_frame_num}. Processing... ---")
            result_image = frame.copy()
            # ... (可視化ロジックは変更なし) ...
            if not parser.rois: break
            frame_h, frame_w = frame.shape[:2]
            scale_w, scale_h = 1.0, 1.0
            if parser.reference_resolution:
                ref_w, ref_h = parser.reference_resolution.get("width", frame_w), parser.reference_resolution.get("height", frame_h)
                scale_w, scale_h = frame_w / ref_w, frame_h / ref_h
            for key, roi_orig in parser.rois.items():
                rois_to_process = roi_orig if isinstance(roi_orig[0], list) else [roi_orig]
                for j, r_orig in enumerate(rois_to_process):
                    try:
                        roi = parser._scale_roi(tuple(r_orig), scale_w, scale_h)
                        x, y, w, h = roi
                        if x + w > frame_w or y + h > frame_h: continue
                        cropped_img = frame[y:y+h, x:x+w]
                        if cropped_img.size == 0: continue
                        preprocessed_img = parser._preprocess_image_for_ocr(cropped_img)
                        config = '--psm 7 -l jpn'
                        text = pytesseract.image_to_string(preprocessed_img, config=config).strip()
                        display_text = f"{parser._find_closest_pokemon_name(text)} (orig: {text})" if key.endswith('_name') else text
                        print(f"  - {key}: {display_text}")
                        cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        text_pos = (x, y - 25) if y - 25 > 0 else (x, y + h + 5)
                        result_image = draw_text_pil(result_image, display_text, text_pos)
                    except Exception as e:
                        print(f"エラー: ROI '{key}' の処理中にエラー: {e}")
            output_path = os.path.join(output_dir, f"verified_scene_{saved_samples + 1}_frame_{current_frame_num}.png")
            cv2.imwrite(output_path, result_image)
            print(f"Result saved to: {output_path}")
            saved_samples += 1
            ocr_triggered_on_static_frame = True

    cap.release()
    print("Verification complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("使用法: python verify_ocr_from_video_.py <video_path>")

