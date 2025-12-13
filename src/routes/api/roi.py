# src/routes/api/roi.py
from flask import Blueprint, request
from src.services.roi_service import RoiService
from src.utils.response_handler import api_success, api_fail, api_error
import logging

roi_bp = Blueprint('roi_api', __name__, url_prefix='/api/roi')
roi_service = RoiService()

@roi_bp.route('/config', methods=['GET'])
def get_roi_config():
    """ROI設定を取得する"""
    try:
        config = roi_service.get_config()
        return api_success(config)
    except Exception as e:
        logging.exception("Failed to get ROI config")
        return api_error("ROI設定の取得に失敗しました。")

@roi_bp.route('/update', methods=['POST'])
def update_roi_config():
    """ROI設定を更新する"""
    try:
        new_config = request.json
        if not new_config:
            return api_fail({"message": "No config data provided"})
        
        roi_service.update_config(new_config)
        return api_success({"message": "ROI configuration updated successfully."})
    except Exception as e:
        logging.exception("Failed to update ROI config")
        return api_error("ROI設定の更新に失敗しました。")

@roi_bp.route('/image_path', methods=['GET'])
def get_roi_image_path():
    """ROI編集に使用する画像のパスを返す"""
    try:
        path_data = roi_service.get_editor_image_path()
        return api_success(path_data)
    except Exception as e:
        logging.exception("Failed to get ROI image path")
        return api_error("ROI画像パスの取得に失敗しました。")