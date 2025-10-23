# src/routes/api/battle.py
from flask import Blueprint, request, jsonify
from src.services.battle_service import BattleService

battle_bp = Blueprint('battle_api', __name__, url_prefix='/api')

@battle_bp.route('/history', methods=['GET'])
def get_history():
    service = BattleService()
    try:
        history_data = service.get_battle_history_and_stats()
        return jsonify(history_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        return jsonify({"message": "対戦結果とログを保存しました。", "log_id": log_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500

@battle_bp.route('/battle/new_id', methods=['GET'])
def get_new_battle_id():
    """新しい連番のバトルIDを生成して返す"""
    service = BattleService()
    try:
        battle_id = service.generate_new_battle_id()
        return jsonify({"battle_id": battle_id})
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500