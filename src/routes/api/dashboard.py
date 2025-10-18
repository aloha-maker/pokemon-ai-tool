# src/routes/api/dashboard.py
from flask import Blueprint, request, jsonify
from src.database.manager import DatabaseManager

dashboard_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('', methods=['GET'])
def get_dashboard_data():
    """ダッシュボードに必要なデータをまとめて取得する"""
    with DatabaseManager() as db:
        summary = db.get_dashboard_summary()
        opponent_ranking = db.get_opponent_pokemon_ranking()
        win_rate_by_opponent = db.get_win_rate_by_opponent()
        my_selection_rate = db.get_my_pokemon_selection_rate()
        selection_pattern_win_rate = db.get_selection_pattern_win_rate()

        # 勝率が高い・低いで分類
        watch_out_pokemon = sorted([p for p in win_rate_by_opponent if p['win_rate'] < 50], key=lambda x: x['win_rate'])[:10]
        good_at_pokemon = sorted([p for p in win_rate_by_opponent if p['win_rate'] >= 50], key=lambda x: x['win_rate'], reverse=True)[:10]

    return jsonify({
        "summary": summary,
        "opponent_ranking": opponent_ranking,
        "watch_out_pokemon": watch_out_pokemon,
        "good_at_pokemon": good_at_pokemon,
        "my_selection_rate": my_selection_rate,
        "selection_pattern_win_rate": selection_pattern_win_rate
    })

@dashboard_bp.route('/customization', methods=['GET'])
def get_customization_data():
    """指定されたポケモンのカスタマイズランキングを取得する"""
    pokemon_name = request.args.get('pokemon_name')
    if not pokemon_name:
        return jsonify({"error": "pokemon_name is required"}), 400
    
    with DatabaseManager() as db:
        data = db.get_opponent_pokemon_customization_ranking(pokemon_name)
    return jsonify(data)
