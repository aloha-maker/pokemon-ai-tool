# src/routes/api/roi.py
import os
import json
from flask import Blueprint, request, jsonify

roi_bp = Blueprint('roi_api', __name__, url_prefix='/api/roi')

ROI_CONFIG_PATH = 'instance/roi_config.json'

@roi_bp.route('/config', methods=['GET'])
def get_roi_config():
    try:
        if os.path.exists(ROI_CONFIG_PATH):
            with open(ROI_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        else:
            # デフォルトの空のコンフィグを返す
            return jsonify({
                "reference_resolution": {"width": 1280, "height": 720},
                "my_pokemon_name": [0,0,0,0],
                "opponent_pokemon_name": [0,0,0,0],
                "my_pokemon_hp": [0,0,0,0],
                "opponent_pokemon_hp": [0,0,0,0]
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@roi_bp.route('/update', methods=['POST'])
def update_roi_config():
    try:
        new_config = request.json
        # instance フォルダがなければ作成
        os.makedirs(os.path.dirname(ROI_CONFIG_PATH), exist_ok=True)
        with open(ROI_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=4, ensure_ascii=False)
        return jsonify({"message": "ROI configuration updated successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@roi_bp.route('/image_path', methods=['GET'])
def get_roi_image_path():
    # ROI編集に使用する画像のパスを返す
    # リアルタイム解析中の最新画像を利用するのが合理的
    return jsonify({"image_path": "/static/captures/live_capture.png"})
