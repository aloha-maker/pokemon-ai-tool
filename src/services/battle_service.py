# src/services/battle_service.py
import os
import uuid
import sys
import datetime
import json
from threading import Lock
from typing import List, Dict, Optional

from src.extensions import db
from src.models import BattleModel,PartyLogModel,RawBattleEventModel

from src.extensions import executor
from src.schemas.pokemon_battle.battle_log import BattleLog

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
    def __init__(self, app_state):
        self.state = app_state
        self.video_dir = os.path.join(project_root, 'videos')
        self.tasks_lock = Lock()

    # --- Battle History Methods --- #
    def generate_new_battle_id(self) -> str:
        """新しい連番のバトルIDを生成する"""
        now = datetime.datetime.now()
        date_str = now.strftime('%Y%m%d')
        latest_id = self.get_latest_battle_id_for_today(date_str)
        
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

    def get_latest_battle_id_for_today(self, date_str: str) -> str | None:
        """
        指定された日付の最新のバトルIDを取得する (例: BATTLE-20231027-005)
        """
        pattern = f'BATTLE-{date_str}-%'
        log = BattleModel.query.filter(BattleModel.battle_id.like(pattern)).order_by(BattleModel.battle_id.desc()).first()
        return log.battle_id if log else None

    def add_battle_log_from_video(self, video_task_id: str, turn_data: dict) -> int:
        """
        動画解析結果から対戦ログを `battle_logs` テーブルに追加する。
        video_task_id とターンごとのデータ(turn_data)を受け取る。
        戻り値は追加されたレコードのID。
        """
        # battle_data をJSON文字列に変換
        battle_data_json = json.dumps(turn_data, ensure_ascii=False, indent=2)
        try:
            # BattleLogインスタンスを作成
            battle_log = BattleLog.from_dict(battle_data_json)
            
            # 一括保存（BattleLogのsave_to_dbメソッドを使用）
            self.delete_battle(battle_data_json['battle_id'])
            battle_log.save_to_db()
        
            return battle_log
            
        except Exception as e:
            db.session.rollback()
            raise e

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
            self.state.video_tasks[task_id] = {"status": "PENDING", "result": None, "filename": video_file.filename}
        
        executor.submit(self._analyze_video_task, task_id, filepath)
        return task_id

    def get_task_status(self, task_id: str) -> dict:
        """タスクの進捗状況を取得する"""
        with self.tasks_lock:
            task = self.state.video_tasks.get(task_id)
            if not task:
                return None

            response_data = task.copy()
            # 完了またはエラーしたタスクは状態を返した後に辞書から削除する
            if response_data.get('status') in ['DONE', 'ERROR']:
                self.state.video_tasks.pop(task_id, None)
        
        return response_data

    def get_battle_log_by_id(self, log_id: int) -> dict:
        """IDを指定して対戦ログを取得する。"""
        log = BattleLog.query.get(log_id)
        return log.to_dict()

    def get_all_battle_logs(self) -> list[dict]:
        """
        すべての対戦履歴をDBから取得する。
        JSONデータはパースして返す。
        """
        battle_logs = BattleLog.query.order_by(BattleLog.battle_id).all()
        return battle_logs.to_dict()

    def _analyze_video_task(self, task_id: str, filepath: str):
        """バックグラウンドで実行される動画解析タスク"""
        try:
            print(f"[Task {task_id}] OCRベースの動画解析を開始: {filepath}")
            with self.tasks_lock:
                self.state.video_tasks[task_id]["status"] = "PROCESSING"
            
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            os.makedirs(config.PROCESSED_DIR, exist_ok=True)

            pokemon_corrector = PokemonNameCorrector(config.POKEMON_MASTER_PATH)
            ability_corrector = AbilityNameCorrector(config.ABILITY_MASTER_PATH)
            ocr_processor = OCRProcessor(pokemon_corrector, ability_corrector)

            print(f"[Task {task_id}] 動画処理を開始: {filepath}")
            turn_data = process_video(filepath, pokemon_corrector, ability_corrector, ocr_processor)

            # データベースへの保存ロジック
            log_id = self.add_battle_log_from_video(task_id, turn_data)

            with self.tasks_lock:
                self.state.video_tasks[task_id]["status"] = "DONE"
                self.state.video_tasks[task_id]["result"] = {"log_id": log_id}
            print(f"[Task {task_id}] OCRベースの動画解析が完了しました。")

        except Exception as e:
            print(f"[Task {task_id}] OCRベース動画解析中にエラー: {e}")
            import traceback
            traceback.print_exc()
            with self.tasks_lock:
                self.state.video_tasks[task_id]["status"] = "ERROR"
                self.state.video_tasks[task_id]["result"] = {"error": str(e)}
                
    def delete_battle(self, battle_id: str) -> bool:
        """
        バトルを削除（関連するパーティとイベントも削除される）
        
        Args:
            battle_id: バトルID
        
        Returns:
            bool: 削除成功時True、対象が存在しない場合False
            
        Raises:
            sqlalchemy.exc.SQLAlchemyError: DB操作エラー
        """
        try:
            model = BattleModel.query.get(battle_id)
            if model:
                db.session.delete(model)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            raise e

    def create_battle_log(self, 
        battle_data: Dict
    ) -> BattleLog:
        """
        バトルの完全なレコードを一括登録（トランザクション処理）
        バトル情報、パーティ、イベントを同時に登録します。
        
        Args:
            battle_data: バトル基本情報
        
        Returns:
            BattleLog: 登録されたBattleLogインスタンス
            
        Raises:
            sqlalchemy.exc.SQLAlchemyError: DB操作エラー
        """

        try:
            # BattleLogインスタンスを作成
            battle_data["events"] = self.state.shared_game_state["battle_log"].events
            battle_log = BattleLog.from_dict(battle_data)
            
            # 一括保存（BattleLogのsave_to_dbメソッドを使用）
            self.delete_battle(battle_data['battle_id'])
            battle_log.save_to_db()
        
            return battle_log
            
        except Exception as e:
            db.session.rollback()
            raise e

