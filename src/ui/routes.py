
import traceback

from flask import Blueprint, jsonify, request
from src.database.manager import DatabaseManager
from src.core import calculator

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

# --- F-06: パーティ管理 (Parties) ---

@api_bp.route('/parties', methods=['GET'])
def get_parties():
    """登録済みのパーティを一覧で取得する。"""
    try:
        with DatabaseManager() as db:
            parties = db.get_all_parties()
        return jsonify(parties), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties/<int:party_id>', methods=['GET'])
def get_party(party_id):
    """指定したIDのパーティ詳細を取得する。"""
    try:
        with DatabaseManager() as db:
            party = db.get_party_by_id(party_id)
        if party:
            return jsonify(party), 200
        else:
            return jsonify({'error': 'Party not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties', methods=['POST'])
def add_party():
    """新しいパーティを登録する。"""
    data = request.get_json()
    if not data or not data.get('name') or 'members' not in data:
        return jsonify({'error': 'Invalid data: name and members are required.'}), 400
    
    try:
        with DatabaseManager() as db:
            new_id = db.add_party(data)
        return jsonify({'message': 'Party added successfully', 'id': new_id}), 201
    except Exception as e:
        print(f"Error in add_party: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties/<int:party_id>', methods=['PUT'])
def update_party(party_id):
    """指定したIDのパーティ情報を更新する。"""
    data = request.get_json()
    if not data or not data.get('name') or 'members' not in data:
        return jsonify({'error': 'Invalid data: name and members are required.'}), 400

    try:
        with DatabaseManager() as db:
            updated_rows = db.update_party(party_id, data)
        if updated_rows > 0:
            return jsonify({'message': f'Party {party_id} updated successfully'}), 200
        else:
            return jsonify({'error': 'Party not found or no changes made'}), 404
    except Exception as e:
        print(f"Error in update_party: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@api_bp.route('/parties/<int:party_id>', methods=['DELETE'])
def delete_party(party_id):
    """指定したIDのパーティを削除する。"""
    try:
        with DatabaseManager() as db:
            deleted_rows = db.delete_party(party_id)
        if deleted_rows > 0:
            return jsonify({'message': f'Party {party_id} deleted successfully'}), 200
        else:
            return jsonify({'error': 'Party not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- F-07: 計算機 (Calculator) ---

@api_bp.route('/calculate/status', methods=['POST'])
def calculate_status_api():
    """ポケモンのステータス実数値を計算して返す。"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        pokemon_id = data.get('pokemon_id')
        level = int(data.get('level', 50))
        evs = data.get('evs', {})
        # 個体値は常に31で固定
        ivs = {'hp': 31, 'attack': 31, 'defense': 31, 'sp_attack': 31, 'sp_defense': 31, 'speed': 31}
        nature_id = data.get('nature_id')

        with DatabaseManager() as db:
            # 1. 種族値を取得
            cursor = db.get_cursor()
            cursor.execute("SELECT hp, attack, defense, sp_attack, sp_defense, speed FROM pokemons WHERE id = ?", (pokemon_id,))
            base_stats_row = cursor.fetchone()
            if not base_stats_row:
                return jsonify({'error': 'Pokemon not found'}), 404
            base_stats = dict(base_stats_row)

            # 2. 性格補正を取得
            cursor.execute("SELECT increased_stat, decreased_stat FROM natures WHERE id = ?", (nature_id,))
            nature_row = cursor.fetchone()
            nature = dict(nature_row) if nature_row else None

        # 3. 計算実行
        calculated_stats = calculator.calculate_status(base_stats, level, evs, ivs, nature)

        return jsonify(calculated_stats), 200

    except Exception as e:
        print(f"Error in calculate_status_api: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
