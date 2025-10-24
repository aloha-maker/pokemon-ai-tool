from src import state
from src.services.battle_service import BattleService
from src.core.video_processor import VideoProcessor

def analyze_video_task(task_id, filepath):
    """バックグラウンドで実行される動画解析タスク"""
    try:
        print(f"[Task {task_id}] Video analysis started for {filepath}")
        state.video_tasks[task_id]["status"] = "PROCESSING"
        
        # VideoProcessorは、解析結果としてターンデータのdictを返すと想定
        processor = VideoProcessor(filepath)
        turn_data = processor.analyze()

        battle_service = BattleService()
        log_id = battle_service.add_battle_log_from_video(task_id, turn_data)

        state.video_tasks[task_id]["status"] = "DONE"
        state.video_tasks[task_id]["result"] = {"log_id": log_id}
        print(f"[Task {task_id}] Video analysis finished. Log ID: {log_id}")

    except Exception as e:
        print(f"[Task {task_id}] Error during video analysis: {e}")
        state.video_tasks[task_id]["status"] = "ERROR"
        state.video_tasks[task_id]["result"] = {"error": str(e)}
