# src/routes/api/database.py
from flask import Blueprint, jsonify, request
from src.database.manager import DatabaseManager

database_bp = Blueprint('database_api', __name__)

@database_bp.route('/api/db/tables', methods=['GET'])
def get_tables():
    """データベースのテーブル一覧を返す。"""
    try:
        with DatabaseManager() as db:
            tables = db.get_all_tables()
        return jsonify(tables)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@database_bp.route('/api/db/search', methods=['GET'])
def search():
    """指定されたテーブルのデータを検索して返す。"""
    table_name = request.args.get('table', type=str)
    keyword = request.args.get('keyword', default='', type=str)
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=50, type=int)
    
    if not table_name:
        return jsonify({"error": "Table name is required"}), 400
        
    offset = (page - 1) * per_page

    try:
        with DatabaseManager() as db:
            result = db.search_table(table_name, keyword, limit=per_page, offset=offset)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
