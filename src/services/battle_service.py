# src/services/battle_service.py
import os
import uuid
import sys
import datetime
import json
from threading import Lock
from typing import List, Dict, Optional

from src.extensions import db
from src.models.battle_model import BattleModel
from src.models.party_log_model import PartyLogModel
from src.models.raw_battle_event_model import RawBattleEventModel

from src.extensions import executor
from src.database.manager import DatabaseManager
from src.services.dashboard_service import DashboardService
from src.services.master_data_service import MasterDataService

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

    def get_battle_history_and_stats(self) -> dict:
        """対戦履歴と統計情報をまとめて取得する"""
        raw_history = self.get_battle_history()
        # 統計情報はDashboardServiceから取得
        dashboard_service = DashboardService()
        stats = dashboard_service.get_battle_stats()
        return {"raw_history": raw_history, "stats": stats}

    def get_battle_history(self, limit: int = 50) -> list[dict]:
        """対戦履歴の一覧を取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT * FROM battle_logs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            
            # JSONデータをパースして返す
            logs = []
            for row in rows:
                log_data = dict(row)
                if log_data.get('battle_data'):
                    try:
                        log_data['battle_data'] = json.loads(log_data['battle_data'])
                    except (json.JSONDecodeError, TypeError):
                        log_data['battle_data'] = {} # パース失敗時は空のdict
                if log_data.get('opponent_party'):
                    try:
                        log_data['opponent_party'] = json.loads(log_data['opponent_party'])
                    except (json.JSONDecodeError, TypeError):
                        log_data['opponent_party'] = {} # パース失敗時は空のdict
                logs.append(log_data)
            return logs

    # def save_result_with_log(self, battle_id: str, my_party_id: int, my_party: list, opponent_party: list, result: str, raw_events: list) -> int:
    #     """対戦結果とリアルタイムOCRログを保存する"""
    #     if not all([my_party_id, opponent_party, result, battle_id]) or result not in ['win', 'lose']:
    #         raise ValueError("パーティ情報、勝敗結果、またはバトルIDが不正です。")
        
    #     master_data_service = MasterDataService()
    #     with DatabaseManager() as db:
    #         cursor = db.get_cursor()

    #         # --- マスターデータを事前に一括で取得 ---
    #         types_map = {row['id']: row['name_ja'] for row in master_data_service.get_master_data_by_resource('types')}
    #         abilities_map = {row['id']: row['name_ja'] for row in master_data_service.get_master_data_by_resource('abilities')}
    #         moves_map = {row['id']: row['name_ja'] for row in master_data_service.get_master_data_by_resource('moves')}

    #         try:
    #             # 1. battles テーブルに対戦記録を作成または更新
    #             cursor.execute(
    #                 "INSERT OR IGNORE INTO battles (battle_id, result, battle_format) VALUES (?, ?, ?)",
    #                 (battle_id, result, 'シングル')
    #             )
    #             cursor.execute(
    #                 "UPDATE battles SET result = ?, battle_format = ? WHERE battle_id = ?",
    #                 (result, 'シングル', battle_id)
    #             )

    #             # 2. 既存の関連ログを削除 (冪等性を保つため)
    #             cursor.execute("DELETE FROM parties_log WHERE battle_id = ?", (battle_id,))
    #             cursor.execute("DELETE FROM raw_battle_events WHERE battle_id = ?", (battle_id,))

    #             # 3. パーティ処理の内部関数
    #             def _process_party_log(party_list, is_opponent):
    #                 parties_log_tuples = []
    #                 for pokemon in party_list:
    #                     name = pokemon.get('name')
    #                     if not name: continue

    #                     item_name = pokemon.get('item')
    #                     tera_type_id = pokemon.get('terastal_type_id')
    #                     ability_id = pokemon.get('ability_id')

    #                     tera_type_name = types_map.get(int(tera_type_id)) if tera_type_id else None
    #                     ability_name = abilities_map.get(int(ability_id)) if ability_id else None
                        
    #                     move_ids = pokemon.get('moves', [])
    #                     move_names = [moves_map.get(int(move_id)) for move_id in move_ids if move_id in moves_map]
    #                     moves_json = json.dumps(move_names, ensure_ascii=False)

    #                     # pokemons_logに常に新しいレコードとして挿入
    #                     cursor.execute(
    #                         """INSERT INTO pokemons_log (pokemon_name, item, terastal_type, ability, moves)
    #                            VALUES (?, ?, ?, ?, ?)""",
    #                         (name, item_name, tera_type_name, ability_name, moves_json)
    #                     )
    #                     pokemon_id = cursor.lastrowid

    #                     is_selected = 1 if pokemon.get('is_selected') else 0
    #                     parties_log_tuples.append((battle_id, pokemon_id, name, 1 if is_opponent else 0, is_selected))
    #                 return parties_log_tuples

    #             # 4. 自パーティと相手パーティのログを生成・保存
    #             my_parties_log_tuples = _process_party_log(my_party, is_opponent=False)
    #             if my_parties_log_tuples:
    #                 cursor.executemany(
    #                     "INSERT INTO parties_log (battle_id, pokemon_id, pokemon_name, is_opponent, is_selected) VALUES (?, ?, ?, ?, ?)",
    #                     my_parties_log_tuples
    #                 )

    #             opponent_parties_log_tuples = _process_party_log(opponent_party, is_opponent=True)
    #             if opponent_parties_log_tuples:
    #                 cursor.executemany(
    #                     "INSERT INTO parties_log (battle_id, pokemon_id, pokemon_name, is_opponent, is_selected) VALUES (?, ?, ?, ?, ?)",
    #                     opponent_parties_log_tuples
    #                 )

    #             # 6. raw_battle_events テーブルにリアルタイムログを記録
    #             print(raw_events)
    #             if raw_events:
    #                 event_log_data = [
    #                     (battle_id, event['sequence'], event['roi_name'], event['ocr_text']['text'])
    #                     for event in raw_events
    #                 ]
    #                 cursor.executemany(
    #                     "INSERT INTO raw_battle_events (battle_id, sequence, roi_name, ocr_text) VALUES (?, ?, ?, ?)",
    #                     event_log_data
    #                 )

    #             db.conn.commit()
    #             return battle_id
    #         except Exception as e:
    #             db.conn.rollback()
    #             raise e

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
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            pattern = f'BATTLE-{date_str}-%'
            cursor.execute(
                "SELECT battle_id FROM battles WHERE battle_id LIKE ? ORDER BY battle_id DESC LIMIT 1",
                (pattern,)
            )
            row = cursor.fetchone()
            return row['battle_id'] if row else None

    def add_battle_log_from_video(self, video_task_id: str, turn_data: dict) -> int:
        """
        動画解析結果から対戦ログを `battle_logs` テーブルに追加する。
        video_task_id とターンごとのデータ(turn_data)を受け取る。
        戻り値は追加されたレコードのID。
        """
        with DatabaseManager() as db:
            cursor = db.get_cursor()

            # battle_data をJSON文字列に変換
            battle_data_json = json.dumps(turn_data, ensure_ascii=False, indent=2)

            # TODO: 動画からパーティを特定する機能が実装されるまで、暫定的に1をセットする
            my_party_id = 1 

            # 新しいログを挿入
            cursor.execute(
                "INSERT INTO battle_logs (video_task_id, battle_data, result, my_party_id) VALUES (?, ?, ?, ?)",
                (
                    video_task_id,
                    battle_data_json,
                    'unknown', # 解析直後は結果不明
                    my_party_id
                )
            )
            db.conn.commit()
            return cursor.lastrowid

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
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT * FROM battle_logs WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            log_data = dict(row)
            # battle_data と opponent_party はJSON文字列なのでパースする
            if log_data.get('battle_data'):
                try:
                    log_data['battle_data'] = json.loads(log_data['battle_data'])
                except (json.JSONDecodeError, TypeError):
                    log_data['battle_data'] = {}
            if log_data.get('opponent_party'):
                try:
                    log_data['opponent_party'] = json.loads(log_data['opponent_party'])
                except (json.JSONDecodeError, TypeError):
                    log_data['opponent_party'] = {}
                
            return log_data

    def get_all_battle_logs(self) -> list[dict]:
        """
        すべての対戦履歴をDBから取得する。
        JSONデータはパースして返す。
        """
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT * FROM battle_logs ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            logs = []
            for row in rows:
                log_data = dict(row)
                if log_data.get('battle_data'):
                    try:
                        log_data['battle_data'] = json.loads(log_data['battle_data'])
                    except (json.JSONDecodeError, TypeError):
                        log_data['battle_data'] = {}
                if log_data.get('opponent_party'):
                    try:
                        log_data['opponent_party'] = json.loads(log_data['opponent_party'])
                    except (json.JSONDecodeError, TypeError):
                        log_data['opponent_party'] = {}
                logs.append(log_data)
            return logs

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
        battle_data: Dict,
        my_party: List[Dict],
        opponent_party: List[Dict],
        events: List[Dict]
    ) -> BattleLog:
        """
        バトルの完全なレコードを一括登録（トランザクション処理）
        バトル情報、パーティ、イベントを同時に登録します。
        
        Args:
            battle_data: バトル基本情報
                {
                    "battle_id": str (必須),
                    "battle_format": str (必須),
                    "result": str (必須),
                    "season": int,
                    "regulation": str,
                    "my_rank": int,
                    "opponent_rank": int,
                    "memo": str
                }
            my_party: 自分のパーティ情報のリスト
                [{"pokemon_name": str, "is_selected": bool, "pokemon_id": int}, ...]
            opponent_party: 相手のパーティ情報のリスト
                [{"pokemon_name": str, "is_selected": bool, "pokemon_id": int}, ...]
            events: イベント情報のリスト
                [{"sequence": int, "roi_name": str, "ocr_text": str, "phase": str}, ...]
        
        Returns:
            BattleLog: 登録されたBattleLogインスタンス
            
        Raises:
            sqlalchemy.exc.SQLAlchemyError: DB操作エラー
        """

        try:
            # BattleLogインスタンスを作成
            battle_log = BattleLog(
                battle_id=battle_data['battle_id'],
                battle_format=battle_data['battle_format'],
                result=battle_data['result'],
                season=battle_data.get('season'),
                regulation=battle_data.get('regulation'),
                my_rank=battle_data.get('my_rank'),
                opponent_rank=battle_data.get('opponent_rank'),
                memo=battle_data.get('memo')
            )
            
            # 自分のパーティメンバーを追加
            for pokemon in my_party:
                party_member = PartyLogModel(
                    battle_id=battle_log.battle_id,
                    pokemon_name=pokemon['pokemon_name'],
                    is_opponent=False,
                    is_selected=pokemon.get('is_selected', False),
                    is_first=pokemon.get('is_first', False),
                    pokemon_id=pokemon.get('pokemon_id')
                )
                battle_log.parties.append(party_member)
            
            # 相手のパーティメンバーを追加
            for pokemon in opponent_party:
                party_member = PartyLogModel(
                    battle_id=battle_log.battle_id,
                    pokemon_name=pokemon['pokemon_name'],
                    is_opponent=True,
                    is_selected=pokemon.get('is_selected', False),
                    is_first=pokemon.get('is_first', False),
                    pokemon_id=pokemon.get('pokemon_id')
                )
                battle_log.parties.append(party_member)
            
            # イベントを追加
            for event_data in events:
                event = RawBattleEventModel(
                    battle_id=battle_log.battle_id,
                    sequence=event_data['sequence'],
                    roi_name=event_data['roi_name'],
                    ocr_text=event_data.get('ocr_text'),
                    phase=event_data.get('phase')
                )
                battle_log.events.append(event)
            
            # 一括保存（BattleLogのsave_to_dbメソッドを使用）
            self.delete_battle(battle_data['battle_id'])
            battle_log.save_to_db()
        
            return battle_log
            
        except Exception as e:
            db.session.rollback()
            raise e

