# src/routes/api/capture.py
from flask import Blueprint, jsonify
from src.services.capture_service import CaptureService

capture_bp = Blueprint('capture_api', __name__, url_prefix='/api')

@capture_bp.route('/party/recognize_opponent', methods=['POST'])
def recognize_opponent_party():
    """現在のフレームから相手のパーティ6体を認識し、画像を保存する"""
    service = CaptureService()
    result = service.recognize_opponent_party_from_frame()
    
    status_code = result.pop('status_code', 200)
    
    return jsonify(result), status_code