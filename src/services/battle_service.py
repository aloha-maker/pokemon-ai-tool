# src/services/battle_service.py
import os
import uuid
import sys
import datetime
from threading import Lock

from src import state
from src.extensions import executor
from src.database.manager import DatabaseManager

# OCR関連のモジュールをインポート
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, project_root)
from src.core.ocr import config
from src.core.ocr.name_corrector import PokemonNameCorrector, AbilityNameCorrector
from src.core.ocr.ocr_processor import OCRProcessor
from src.core.ocr.video_processor import process_video

class BattleService:
    """
    対戦履歴や動画解析タスクに関連するビジネスロジックを担当するサービスクラス
    """
    def __init__(self):
        self.video_dir = os.path.join(project_root, 'videos')
        self.tasks_lock = Lock()

    # --- Battle History Methods --- #

    def get_battle_history_and_stats(self) -> dict:
        """対戦履歴と統計情報をまとめて取得する"""
        with DatabaseManager() as db:
            raw_history = db.get_battle_history()
            stats = db.get_battle_stats()
        return {"raw_history": raw_history, "stats": stats}

    def add_log(self, data: dict) -> int:
        """対戦ログを追加する"""
        with DatabaseManager() as db:
            log_id = db.add_battle_log(data)
        return log_id

    def save_result(self, my_party_id: int, opponent_party: list, result: str) -> int:
        """対戦結果を保存する"""
        if not all([my_party_id, opponent_party, result]) or result not in ['win', 'lose']:
            raise ValueError("パーティ情報または勝敗結果が不正です。")
        with DatabaseManager() as db:
            log_id = db.save_battle_result(my_party_id, opponent_party, result)
        return log_id

    def save_result_with_log(self, battle_id: str, my_party_id: int, my_party: list, opponent_party: list, result: str, raw_events: list) -> int:
        """対戦結果とリアルタイムOCRログを保存する"""
        if not all([my_party_id, opponent_party, result, battle_id]) or result not in ['win', 'lose']:
            raise ValueError("パーティ情報、勝敗結果、またはバトルIDが不正です。")
        with DatabaseManager() as db:
            log_id = db.save_battle_result_with_log(battle_id, my_party_id, my_party, opponent_party, result, raw_events)
        return log_id

    def prepare_log(self, my_party_id: int, opponent_party: list) -> int:
        """対戦前のパーティ情報を保存する"""
        if not my_party_id or not isinstance(opponent_party, list) or len(opponent_party) == 0:
            raise ValueError("パーティ情報が不正です。")
        with DatabaseManager() as db:
            log_id = db.prepare_battle_log(my_party_id, opponent_party)
        return log_id

    def generate_new_battle_id(self) -> str:
        """新しい連番のバトルIDを生成する"""
        with DatabaseManager() as db:
            now = datetime.datetime.now()
            date_str = now.strftime('%Y%m%d')
            latest_id = db.get_latest_battle_id_for_today(date_str)
            
            if latest_id:
                try:
                    last_seq = int(latest_id.split('-')[-1])
                    new_seq = last_seq + 1
                except (ValueError, IndexError):
                    new_seq = 1
            else:
                new_seq = 1
            
            seq_str = f'{new_seq:04}'
            return f'BATTLE-{date_str}-{seq_str}'

    # --- Video Analysis Methods --- #

    def submit_video_analysis(self, video_file) -> str:
        """動画ファイルを保存し、非同期の解析タスクを開始する"""
        if not video_file or video_file.filename == '':
            raise ValueError("No selected file")

        task_id = str(uuid.uuid4())
        filename = f"{task_id}_{video_file.filename}"
        
        os.makedirs(self.video_dir, exist_ok=True)
        filepath = os.path.join(self.video_dir, filename)
        video_file.save(filepath)
        
        with self.tasks_lock:
            state.video_tasks[task_id] = {"status": "PENDING", "result": None, "filename": video_file.filename}
        
        executor.submit(self._analyze_video_task, task_id, filepath)
        return task_id

    def get_task_status(self, task_id: str) -> dict:
        """タスクの進捗状況を取得する"""
        with self.tasks_lock:
            task = state.video_tasks.get(task_id)
            if not task:
                return None

            response_data = task.copy()
            # 完了またはエラーしたタスクは状態を返した後に辞書から削除する
            if response_data.get('status') in ['DONE', 'ERROR']:
                state.video_tasks.pop(task_id, None)
        
        return response_data

    def get_log_by_id(self, log_id: int) -> dict:
        """IDを指定して対戦ログを取得する"""
        with DatabaseManager() as db:
            log = db.get_battle_log_by_id(log_id)
        return log

    def _analyze_video_task(self, task_id: str, filepath: str):
        """バックグラウンドで実行される動画解析タスク"""
        try:
            print(f"[Task {task_id}] OCRベースの動画解析を開始: {filepath}")
            with self.tasks_lock:
                state.video_tasks[task_id]["status"] = "PROCESSING"
            
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            os.makedirs(config.PROCESSED_DIR, exist_ok=True)

            pokemon_corrector = PokemonNameCorrector(config.POKEMON_MASTER_PATH)
            ability_corrector = AbilityNameCorrector(config.ABILITY_MASTER_PATH)
            ocr_processor = OCRProcessor(pokemon_corrector, ability_corrector)

            print(f"[Task {task_id}] 動画処理を開始: {filepath}")
            turn_data = process_video(filepath, pokemon_corrector, ability_corrector, ocr_processor)

            # データベースへの保存ロジックは未実装のためコメントアウト
            # log_id = None
            # with DatabaseManager() as db:
            #     log_id = db.add_battle_log_from_video(task_id, turn_data)

            with self.tasks_lock:
                state.video_tasks[task_id]["status"] = "DONE"
                # state.video_tasks[task_id]["result"] = {"log_id": log_id}
                state.video_tasks[task_id]["result"] = {"message": "解析成功（DB保存は未実装）"}
            print(f"[Task {task_id}] OCRベースの動画解析が完了しました。")

        except Exception as e:
            print(f"[Task {task_id}] OCRベース動画解析中にエラー: {e}")
            import traceback
            traceback.print_exc()
            with self.tasks_lock:
                state.video_tasks[task_id]["status"] = "ERROR"
                state.video_tasks[task_id]["result"] = {"error": str(e)}
