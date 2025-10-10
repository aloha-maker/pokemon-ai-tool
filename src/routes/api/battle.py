# src/routes/api/battle.py
from flask import Blueprint, request, jsonify
from src.database.manager import DatabaseManager

battle_bp = Blueprint('battle_api', __name__, url_prefix='/api')

@battle_bp.route('/history/add', methods=['POST'])
def add_history():
    data = request.json
    try:
        with DatabaseManager() as db:
            db.add_battle_log(data)
        return jsonify({"message": "対戦履歴を保存しました。"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@battle_bp.route('/history', methods=['GET'])
def get_history():
    try:
        with DatabaseManager() as db:
            raw_history = db.get_battle_history()
            stats = db.get_battle_stats()

        return jsonify({
            "raw_history": raw_history,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@battle_bp.route('/battles/save_result', methods=['POST'])
def save_battle_result():
    """対戦結果をDBに保存する"""
    data = request.json
    my_party_id = data.get('my_party_id')
    opponent_party = data.get('opponent_party')
    result = data.get('result') # 'win' or 'lose'

    if not all([my_party_id, opponent_party, result]) or result not in ['win', 'lose']:
        return jsonify({"error": "パーティ情報または勝敗結果が不正です。"}), 400

    try:
        with DatabaseManager() as db:
            log_id = db.save_battle_result(my_party_id, opponent_party, result)
        return jsonify({"message": "対戦結果を保存しました。", "log_id": log_id}), 201
    except Exception as e:
        return jsonify({"error": f"データベースへの保存中にエラーが発生しました: {str(e)}"}), 500


@battle_bp.route('/battles/save_result_with_log', methods=['POST'])
def save_battle_result_with_log():
    """対戦結果とリアルタイムOCRログをDBに保存する"""
    data = request.json
    my_party_id = data.get('my_party_id')
    opponent_party = data.get('opponent_party')
    result = data.get('result')
    raw_events = data.get('raw_events', []) # ログデータ

    if not all([my_party_id, opponent_party, result]) or result not in ['win', 'lose']:
        return jsonify({"error": "パーティ情報または勝敗結果が不正です。"}), 400

    try:
        with DatabaseManager() as db:
            battle_id = db.save_battle_result_with_log(my_party_id, opponent_party, result, raw_events)
        return jsonify({"message": "対戦結果とログを保存しました。", "battle_id": battle_id}), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"データベースへの保存中にエラーが発生しました: {str(e)}"}), 500


@battle_bp.route('/battles/prepare', methods=['POST'])
def prepare_battle():
    """対戦前のパーティ情報をDBに保存する"""
    data = request.json
    my_party_id = data.get('my_party_id')
    opponent_party = data.get('opponent_party')

    if not my_party_id or not isinstance(opponent_party, list) or len(opponent_party) == 0:
        return jsonify({"error": "パーティ情報が不正です。"}), 400

    try:
        with DatabaseManager() as db:
            log_id = db.prepare_battle_log(my_party_id, opponent_party)
        return jsonify({"message": "対戦パーティを保存しました。", "log_id": log_id}), 201
    except Exception as e:
        return jsonify({"error": f"データベースへの保存中にエラーが発生しました: {str(e)}"}), 500
