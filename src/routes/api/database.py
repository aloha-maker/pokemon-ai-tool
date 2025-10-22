# src/routes/api/database.py
from flask import Blueprint, jsonify, request
from src.services.master_data_service import MasterDataService

database_bp = Blueprint('database_api', __name__)
service = MasterDataService()

@database_bp.route('/api/db/tables', methods=['GET'])
def get_tables():
    """データベースのテーブル一覧を返す。"""
    tables = service.get_all_table_names()
    return jsonify(tables)

@database_bp.route('/api/db/search', methods=['GET'])
def search():
    """指定されたテーブルのデータを検索して返す。"""
    table_name = request.args.get('table', type=str)
    keyword = request.args.get('keyword', default='', type=str)
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=50, type=int)
    
    try:
        result = service.search_table(table_name, keyword, page, per_page)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
