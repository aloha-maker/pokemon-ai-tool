# src/routes/api/dashboard.py
from flask import Blueprint, request, jsonify
from src.services.dashboard_service import DashboardService

dashboard_bp = Blueprint('dashboard_api', __name__, url_prefix='/api/dashboard')
dashboard_service = DashboardService()

@dashboard_bp.route('', methods=['GET'])
def get_dashboard_data():
    """ダッシュボードに必要なデータをまとめて取得する"""
    try:
        data = dashboard_service.get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        # TODO: P0のタスクとして中央集権的なエラーハンドラとロギングを導入する
        # import logging
        # logging.exception(e)
        return jsonify({"error": "An internal server error occurred"}), 500

@dashboard_bp.route('/customization', methods=['GET'])
def get_customization_data():
    """指定されたポケモンのカスタマイズランキングを取得する"""
    pokemon_name = request.args.get('pokemon_name')
    
    try:
        data = dashboard_service.get_customization_data(pokemon_name)
        return jsonify(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # TODO: P0のタスクとして中央集権的なエラーハンドラとロギングを導入する
        # import logging
        # logging.exception(e)
        return jsonify({"error": "An internal server error occurred"}), 500
