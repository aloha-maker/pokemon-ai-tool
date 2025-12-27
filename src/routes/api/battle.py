# src/routes/api/battle.py
import logging
import json
from flask import Blueprint, request, current_app
from src.services.battle_service import BattleService
from src.utils.response_handler import api_success, api_fail, api_error

battle_bp = Blueprint('battle_api', __name__, url_prefix='/api')

@battle_bp.route('/battles/save_result_with_log', methods=['POST'])
def save_battle_result_with_log():
    """対戦結果とリアルタイムOCRログをDBに保存する"""
    service = BattleService(current_app.state)
    data = request.json

    # バトルデータの準備
    battle_data = {
        "battle_id": data.get('battle_id'),
        "battle_format": "シングル",
        "result": data.get('result'),
        "season": 34,
        "regulation": "レギュレーションJ",
        "my_rank": 0,
        "opponent_rank": 0,
        "memo": "",
        "parties": [data.get('my_party'),data.get('opponent_party')]
    }
    
    try:        
        battle_log = service.create_battle_log(battle_data)

        return api_success({"message": "対戦結果とログを保存しました。", "log_id": battle_log.battle_id}, status_code=201)
    except ValueError as e:
        return api_fail({"error": str(e)})
    except Exception as e:
        logging.exception(f"対戦結果の保存中に予期せぬエラーが発生しました: {e}")
        return api_error("サーバー内部でエラーが発生しました。")

@battle_bp.route('/battle/new_id', methods=['GET'])
def get_new_battle_id():
    """新しい連番のバトルIDを生成して返す"""
    service = BattleService(current_app.state)
    try:
        battle_id = service.generate_new_battle_id()
        return api_success({"battle_id": battle_id})
    except Exception as e:
        logging.exception(f"新規バトルIDの生成中にエラーが発生しました: {e}")
        return api_error("新規バトルIDの生成に失敗しました。")