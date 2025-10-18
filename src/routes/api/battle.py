# src/routes/api/battle.py
from flask import Blueprint, request, jsonify
from src.database.manager import DatabaseManager
import datetime

battle_bp = Blueprint('battle_api', __name__, url_prefix='/api')

@battle_bp.route('/history/add', methods=['POST'])
def add_history():
    data = request.json
    with DatabaseManager() as db:
        db.add_battle_log(data)
    return jsonify({"message": "対戦履歴を保存しました。"}), 201

@battle_bp.route('/history', methods=['GET'])
def get_history():
    with DatabaseManager() as db:
        raw_history = db.get_battle_history()
        stats = db.get_battle_stats()

    return jsonify({
        "raw_history": raw_history,
        "stats": stats
    })

@battle_bp.route('/battles/save_result', methods=['POST'])
def save_battle_result():
    """対戦結果をDBに保存する"""
    data = request.json
    my_party_id = data.get('my_party_id')
    opponent_party = data.get('opponent_party')
    result = data.get('result') # 'win' or 'lose'

    if not all([my_party_id, opponent_party, result]) or result not in ['win', 'lose']:
        return jsonify({"error": "パーティ情報または勝敗結果が不正です。"}), 400

    with DatabaseManager() as db:
        log_id = db.save_battle_result(my_party_id, opponent_party, result)
    return jsonify({"message": "対戦結果を保存しました。", "log_id": log_id}), 201


@battle_bp.route('/battles/save_result_with_log', methods=['POST'])
def save_battle_result_with_log():
    """対戦結果とリアルタイムOCRログをDBに保存する"""
    data = request.json
    my_party_id = data.get('my_party_id')
    my_party = data.get('my_party', [])
    opponent_party = data.get('opponent_party')
    result = data.get('result')
    raw_events = data.get('raw_events', []) # ログデータ
    battle_id = data.get('battle_id') # バトルIDをリクエストから取得

    # battle_idも必須項目とする
    if not all([my_party_id, opponent_party, result, battle_id]) or result not in ['win', 'lose']:
        return jsonify({"error": "パーティ情報、勝敗結果、またはバトルIDが不正です。"}), 400

    with DatabaseManager() as db:
        # battle_idとmy_partyをDB保存メソッドに渡す
        log_id = db.save_battle_result_with_log(battle_id, my_party_id, my_party, opponent_party, result, raw_events)
    return jsonify({"message": "対戦結果とログを保存しました。", "log_id": log_id}), 201


@battle_bp.route('/battles/prepare', methods=['POST'])
def prepare_battle():
    """対戦前のパーティ情報をDBに保存する"""
    data = request.json
    my_party_id = data.get('my_party_id')
    opponent_party = data.get('opponent_party')

    if not my_party_id or not isinstance(opponent_party, list) or len(opponent_party) == 0:
        return jsonify({"error": "パーティ情報が不正です。"}), 400

    with DatabaseManager() as db:
        log_id = db.prepare_battle_log(my_party_id, opponent_party)
    return jsonify({"message": "対戦パーティを保存しました。", "log_id": log_id}), 201


@battle_bp.route('/battle/new_id', methods=['GET'])
def get_new_battle_id():
    """新しい連番のバトルIDを生成して返す"""
    with DatabaseManager() as db:
        now = datetime.datetime.now()
        date_str = now.strftime('%Y%m%d')
        
        latest_id = db.get_latest_battle_id_for_today(date_str)
        
        if latest_id:
            # IDからシーケンス番号を抽出
            try:
                last_seq = int(latest_id.split('-')[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                # フォーマットが不正な場合は1から始める
                new_seq = 1
        else:
            # 今日最初のID
            new_seq = 1
        
        # 4桁のゼロ埋め
        seq_str = f'{new_seq:04}'
        
        battle_id = f'BATTLE-{date_str}-{seq_str}'
        return jsonify({"battle_id": battle_id})
