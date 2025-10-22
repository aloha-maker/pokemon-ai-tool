# src/routes/api/video.py
from flask import Blueprint, request, jsonify
from src.services.battle_service import BattleService

video_bp = Blueprint('video_api', __name__, url_prefix='/api/videos')

@video_bp.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    service = BattleService()
    try:
        task_id = service.submit_video_analysis(request.files['video'])
        return jsonify({"message": "Video uploaded successfully. Analysis started.", "task_id": task_id}), 202
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # TODO: Add logging
        return jsonify({"error": "An internal server error occurred"}), 500

@video_bp.route('/status/<task_id>', methods=['GET'])
def get_video_status(task_id):
    service = BattleService()
    task = service.get_task_status(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@video_bp.route('/result/<int:log_id>', methods=['GET'])
def get_video_result(log_id):
    service = BattleService()
    log = service.get_log_by_id(log_id)
    if not log:
        return jsonify({"error": "Log not found"}), 404
    return jsonify(log)