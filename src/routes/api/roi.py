# src/routes/api/roi.py
from flask import Blueprint, request, jsonify
from src.services.roi_service import RoiService

roi_bp = Blueprint('roi_api', __name__, url_prefix='/api/roi')
# TODO: config_pathはFlaskのapp.configから取得するようにP0タスクで修正する
roi_service = RoiService(config_path='instance/roi_config.json')

@roi_bp.route('/config', methods=['GET'])
def get_roi_config():
    """ROI設定を取得する"""
    try:
        config = roi_service.get_config()
        return jsonify(config)
    except RuntimeError as e:
        # logging.exception(e)
        return jsonify({"error": str(e)}), 500

@roi_bp.route('/update', methods=['POST'])
def update_roi_config():
    """ROI設定を更新する"""
    new_config = request.json
    if not new_config:
        return jsonify({"error": "No config data provided"}), 400
        
    try:
        roi_service.update_config(new_config)
        return jsonify({"message": "ROI configuration updated successfully."})
    except (TypeError, RuntimeError) as e:
        # logging.exception(e)
        return jsonify({"error": str(e)}), 400

@roi_bp.route('/image_path', methods=['GET'])
def get_roi_image_path():
    """ROI編集に使用する画像のパスを返す"""
    # このエンドポイントは単純なため、当面はエラーハンドリングを省略
    path_data = roi_service.get_editor_image_path()
    return jsonify(path_data)