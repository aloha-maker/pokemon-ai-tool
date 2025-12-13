# src/routes/api/video.py
import logging
from flask import Blueprint, request, current_app
from src.services.battle_service import BattleService
from src.utils.response_handler import api_success, api_fail, api_error

video_bp = Blueprint('video_api', __name__, url_prefix='/api/videos')

@video_bp.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return api_fail({"error": "No video file provided"})
    
    service = BattleService(current_app.state)
    try:
        task_id = service.submit_video_analysis(request.files['video'])
        return api_success({"message": "Video uploaded successfully. Analysis started.", "task_id": task_id}, status_code=202)
    except ValueError as e:
        return api_fail({"error": str(e)})
    except Exception as e:
        logging.exception(f"動画アップロード処理中に予期せぬエラーが発生しました: {e}")
        return api_error("サーバー内部でエラーが発生しました。")

@video_bp.route('/status/<task_id>', methods=['GET'])
def get_video_status(task_id):
    service = BattleService(current_app.state)
    try:
        task = service.get_task_status(task_id)
        if not task:
            return api_fail({"error": "Task not found"}, status_code=404)
        return api_success(task)
    except Exception as e:
        logging.exception(f"タスクステータスの取得中にエラーが発生しました: {e}")
        return api_error("ステータスの取得に失敗しました。")

@video_bp.route('/result/<log_id>', methods=['GET'])
def get_video_result(log_id):
    service = BattleService(current_app.state)
    try:
        log = service.get_battle_log_by_id(log_id)
        if not log:
            return api_fail({"error": "Log not found"}, status_code=404)
        return api_success(log)
    except Exception as e:
        logging.exception(f"動画解析結果の取得中にエラーが発生しました: {e}")
        return api_error("解析結果の取得に失敗しました。")