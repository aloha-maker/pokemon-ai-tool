# src/routes/api/battle.py
import logging
from flask import Blueprint, request
from src.services.battle_service import BattleService
from src.utils.response_handler import api_success, api_fail, api_error

battle_bp = Blueprint('battle_api', __name__, url_prefix='/api')

@battle_bp.route('/history', methods=['GET'])
def get_history():
    """対戦履歴と統計情報を取得する"""
    service = BattleService()
    try:
        history_data = service.get_battle_history_and_stats()
        return api_success(history_data)
    except Exception as e:
        logging.exception(f"対戦履歴の取得中にエラーが発生しました: {e}")
        return api_error("対戦履歴の取得に失敗しました。")

@battle_bp.route('/battles/save_result_with_log', methods=['POST'])
def save_battle_result_with_log():
    """対戦結果とリアルタイムOCRログをDBに保存する"""
    service = BattleService()
    data = request.json
    try:
        log_id = service.save_result_with_log(
            battle_id=data.get('battle_id'),
            my_party_id=data.get('my_party_id'),
            my_party=data.get('my_party', []),
            opponent_party=data.get('opponent_party'),
            result=data.get('result'),
            raw_events=data.get('raw_events', [])
        )
        return api_success({"message": "対戦結果とログを保存しました。", "log_id": log_id}, status_code=201)
    except ValueError as e:
        return api_fail({"error": str(e)})
    except Exception as e:
        logging.exception(f"対戦結果の保存中に予期せぬエラーが発生しました: {e}")
        return api_error("サーバー内部でエラーが発生しました。")

@battle_bp.route('/battle/new_id', methods=['GET'])
def get_new_battle_id():
    """新しい連番のバトルIDを生成して返す"""
    service = BattleService()
    try:
        battle_id = service.generate_new_battle_id()
        return api_success({"battle_id": battle_id})
    except Exception as e:
        logging.exception(f"新規バトルIDの生成中にエラーが発生しました: {e}")
        return api_error("新規バトルIDの生成に失敗しました。")