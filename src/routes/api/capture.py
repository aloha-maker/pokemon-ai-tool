# src/routes/api/capture.py
import os
import time
import cv2
import pygetwindow
import json
from flask import Blueprint, request, jsonify, current_app
from src.core.capture import ScreenCapturer
from src.core.ocr.ocr_processor import OCRProcessor

capture_bp = Blueprint('capture_api', __name__, url_prefix='/api')

DEBUG_IMAGE_DIR = '.img'
ROI_CONFIG_PATH = 'instance/roi_config.json'

@capture_bp.route('/capture', methods=['POST'])
def capture_window():
    data = request.get_json()
    if not data or 'window_title' not in data:
        return jsonify({"error": "window_title is required."} ), 400

    window_title = data['window_title']
    region = data.get('region')

    capturer = ScreenCapturer(window_title)
    
    if not capturer._find_window():
        return jsonify({"error": f"Window '{window_title}' not found."} ), 404

    frame = capturer.capture_frame(region=region)

    if frame is None:
        return jsonify({"error": "Failed to capture frame."} ), 500

    captures_dir = os.path.join('static', 'captures')
    filename = f"captured_{int(time.time())}.png"
    filepath = os.path.join(captures_dir, filename)
    
    cv2.imwrite(filepath, frame)
    
    return jsonify({
        "message": "Capture successful.",
        "file_path": filepath.replace('\\', '/')
    })

@capture_bp.route('/ocr_test', methods=['POST'])
def ocr_test():
    data = request.get_json()
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path is required."}), 400

    image_path = data['image_path']
    if not os.path.exists(image_path):
        return jsonify({"error": f"Image not found at '{image_path}'"}), 404

    img = cv2.imread(image_path)
    if img is None:
        return jsonify({"error": f"Failed to read image from '{image_path}'"}), 500

    parser = OCRProcessor()
    game_state = parser.parse_frame(img)

    return jsonify({
        "message": "OCR process completed.",
        "ocr_results": game_state
    })

@capture_bp.route('/windows', methods=['GET'])
def get_windows():
    titles = pygetwindow.getAllTitles()
    window_titles = [title for title in titles if title]
    return jsonify({"windows": window_titles})

@capture_bp.route('/party/recognize_opponent', methods=['POST'])
def recognize_opponent_party():
    """現在のフレームから相手のパーティ6体を認識し、画像を保存する"""
    latest_frame_path = 'static/captures/latest_frame.jpg'

    if not os.path.exists(latest_frame_path):
        return jsonify({"success": False, "error": "キャプチャ画像が見つかりません。リアルタイム解析が実行されているか確認してください。"}), 404

    frame = cv2.imread(latest_frame_path)
    if frame is None:
        return jsonify({"success": False, "error": "キャプチャ画像の読み込みに失敗しました。"}), 500

    # タイムスタンプで今回処理用のフォルダを作成
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_dir_for_this_run = os.path.join(DEBUG_IMAGE_DIR, timestamp)
    os.makedirs(output_dir_for_this_run, exist_ok=True)

    # 切り抜き前の全体画像を保存
    full_frame_save_path = os.path.join(output_dir_for_this_run, "full_frame.jpg")
    cv2.imwrite(full_frame_save_path, frame)

    with open(ROI_CONFIG_PATH, 'r', encoding='utf-8') as f:
        roi_config = json.load(f)

    party_rois = [
        roi_config.get(f'your_poke{i}') for i in range(1, 7)
    ]

    recognized_party = []
    debug_info = []
    roi_names = [f'your_poke{i}' for i in range(1, 7)]

    for i, roi in enumerate(party_rois):
        roi_name = roi_names[i]
        pokemon_name = ""
        recognition_details = {}

        if roi and isinstance(roi, list) and len(roi) == 4:
            x, y, w, h = roi
            roi_image = frame[y:y+h, x:x+w]

            if roi_image.size > 0:
                # 切り抜いたROI画像を保存
                roi_filename = f"{roi_name}.png"
                roi_save_path = os.path.join(output_dir_for_this_run, roi_filename)
                cv2.imwrite(roi_save_path, roi_image)

            recognition_details = current_app.pokemon_recognizer.recognize(roi_image)
            pokemon_name = recognition_details.get("name", "")
        
        recognized_party.append(pokemon_name)
        debug_info.append({
            "roi": roi_name,
            "recognized_name": pokemon_name,
            "best_match_template": recognition_details.get("template_name", ""),
            "score": round(recognition_details.get("score", 0.0), 4)
        })
    
    return jsonify({"success": True, "party": recognized_party, "debug_info": debug_info})
