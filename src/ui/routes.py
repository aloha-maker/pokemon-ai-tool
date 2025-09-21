
from flask import Blueprint, jsonify, request
from src.database.manager import DatabaseManager

# APIエンドポイント用のBlueprintを作成
api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- F-05: 育成済みポケモン管理 (Trained Pokemons) ---

@api_bp.route('/trained-pokemons', methods=['GET'])
def get_trained_pokemons():
    """登録済みの育成済みポケモンを一覧で取得する。"""
    try:
        with DatabaseManager() as db:
            pokemons = db.get_all_trained_pokemons()
        return jsonify(pokemons), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['GET'])
def get_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモンの詳細を取得する。"""
    try:
        with DatabaseManager() as db:
            pokemon = db.get_trained_pokemon_by_id(pokemon_id)
        if pokemon:
            return jsonify(pokemon), 200
        else:
            return jsonify({'error': 'Pokemon not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trained-pokemons', methods=['POST'])
def add_trained_pokemon():
    """新しい育成済みポケモンを登録する。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400
    
    try:
        with DatabaseManager() as db:
            new_id = db.add_trained_pokemon(data)
        return jsonify({'message': 'Pokemon added successfully', 'id': new_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['PUT'])
def update_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモン情報を更新する。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        with DatabaseManager() as db:
            updated_rows = db.update_trained_pokemon(pokemon_id, data)
        if updated_rows > 0:
            return jsonify({'message': f'Pokemon {pokemon_id} updated successfully'}), 200
        else:
            return jsonify({'error': 'Pokemon not found or no changes made'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trained-pokemons/<int:pokemon_id>', methods=['DELETE'])
def delete_trained_pokemon(pokemon_id):
    """指定したIDの育成済みポケモンを削除する。"""
    try:
        with DatabaseManager() as db:
            deleted_rows = db.delete_trained_pokemon(pokemon_id)
        if deleted_rows > 0:
            return jsonify({'message': f'Pokemon {pokemon_id} deleted successfully'}), 200
        else:
            return jsonify({'error': 'Pokemon not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Master Data API Endpoints ---

@api_bp.route('/master/<resource>', methods=['GET'])
def get_master_data(resource):
    """ポケモン、技、特性などのマスターデータを取得する。"""
    valid_resources = ['pokemons', 'moves', 'items', 'abilities', 'natures', 'types']
    if resource not in valid_resources:
        return jsonify({'error': 'Invalid resource specified'}), 404

    try:
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            # name_ja がないテーブル (moves) のために name を使う
            if resource in ['moves']:
                 cursor.execute(f"SELECT id, name as name_ja FROM {resource} ORDER BY id")
            else:
                 cursor.execute(f"SELECT id, name_ja FROM {resource} ORDER BY name_ja")
            items = cursor.fetchall()
        return jsonify([dict(item) for item in items]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
