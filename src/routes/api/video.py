# src/routes/api/video.py
import os
import uuid
import sys
from flask import Blueprint, request, jsonify

from src import state
from src.extensions import executor
from src.database.manager import DatabaseManager

# プロジェクトルートをシステムパスに追加
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
sys.path.insert(0, project_root)

from src.core.ocr import config
from src.core.ocr.name_corrector import PokemonNameCorrector, AbilityNameCorrector
from src.core.ocr.ocr_processor import OCRProcessor
from src.core.ocr.video_processor import process_video

video_bp = Blueprint('video_api', __name__, url_prefix='/api/videos')

VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'videos')

def analyze_video_task(task_id, filepath):
    """バックグラウンドで実行される動画解析タスク - OCRベース版"""
    try:            
        print(f"[Task {task_id}] OCRベースの動画解析を開始: {filepath}")
        state.video_tasks[task_id]["status"] = "PROCESSING"
        
        # 出力ディレクトリの事前作成
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(config.PROCESSED_DIR, exist_ok=True)

        # 名前補正クラスとOCRプロセッサーの初期化
        pokemon_corrector = PokemonNameCorrector(config.POKEMON_MASTER_PATH)
        ability_corrector = AbilityNameCorrector(config.ABILITY_MASTER_PATH)
        ocr_processor = OCRProcessor(pokemon_corrector, ability_corrector)

        # 動画処理の実行
        print(f"[Task {task_id}] 動画処理を開始: {filepath}")
        turn_data = process_video(filepath, pokemon_corrector, ability_corrector, ocr_processor)

        # # データベースへの保存
        # log_id = None
        # with DatabaseManager() as db:
        #     log_id = db.add_battle_log_from_video(task_id, turn_data)

        # state.video_tasks[task_id]["status"] = "DONE"
        # state.video_tasks[task_id]["result"] = {"log_id": log_id}
        # print(f"[Task {task_id}] OCRベースの動画解析が完了しました。Log ID: {log_id}")

    except Exception as e:
        print(f"[Task {task_id}] OCRベース動画解析中にエラー: {e}")
        import traceback
        traceback.print_exc()
        state.video_tasks[task_id]["status"] = "ERROR"
        state.video_tasks[task_id]["result"] = {"error": str(e)}

@video_bp.route('/upload', methods=['POST'])
def upload_video():
        
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    task_id = str(uuid.uuid4())
    filename = f"{task_id}_{file.filename}"
    
    os.makedirs(VIDEO_DIR, exist_ok=True)
    filepath = os.path.join(VIDEO_DIR, filename)

    try:
        file.save(filepath)
        
        state.video_tasks[task_id] = {"status": "PENDING", "result": None, "filename": file.filename}
        
        executor.submit(analyze_video_task, task_id, filepath)

        return jsonify({"message": "Video uploaded successfully. Analysis started.", "task_id": task_id}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@video_bp.route('/status/<task_id>', methods=['GET'])
def get_video_status(task_id):
    task = state.video_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@video_bp.route('/result/<int:log_id>', methods=['GET'])
def get_video_result(log_id):
    try:
        with DatabaseManager() as db:
            log = db.get_battle_log_by_id(log_id)
            if not log:
                return jsonify({"error": "Log not found"}), 404
            return jsonify(log)
    except Exception as e:
        return jsonify({"error": str(e)}), 500