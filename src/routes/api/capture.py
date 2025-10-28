# src/routes/api/capture.py
import logging
from flask import Blueprint
from src.services.capture_service import CaptureService
from src.utils.response_handler import api_success, api_fail, api_error

capture_bp = Blueprint('capture_api', __name__, url_prefix='/api')

@capture_bp.route('/party/recognize_opponent', methods=['POST'])
def recognize_opponent_party():
    """現在のフレームから相手のパーティ6体を認識し、画像を保存する"""
    service = CaptureService()
    try:
        result = service.recognize_opponent_party_from_frame()
        
        if result.get('success'):
            # 成功した場合
            response_data = {
                "party": result.get("party"),
                "debug_info": result.get("debug_info")
            }
            return api_success(response_data)
        else:
            # サービス内で制御されたエラーの場合
            error_message = result.get("error", "不明なエラーが発生しました。")
            status_code = result.get("status_code", 400)
            return api_fail({"error": error_message}, status_code=status_code)

    except Exception as e:
        logging.exception(f"相手パーティの認識中に予期せぬエラーが発生しました: {e}")
        return api_error("サーバー内部でエラーが発生しました。")