# src/routes/api/trained_pokemon.py
from flask import Blueprint, request, jsonify
from src.database.manager import DatabaseManager

trained_pokemon_bp = Blueprint('trained_pokemon_api', __name__, url_prefix='/api/trained-pokemons')

@trained_pokemon_bp.route('', methods=['GET'])
def get_trained_pokemons():
    """育成済みポケモンの一覧を取得する"""
    try:
        with DatabaseManager() as db:
            pokemons = db.get_all_trained_pokemons()
        return jsonify(pokemons)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@trained_pokemon_bp.route('/<int:pokemon_id>', methods=['GET'])
def get_trained_pokemon(pokemon_id):
    """単一の育成済みポケモン情報を取得する"""
    try:
        with DatabaseManager() as db:
            pokemon = db.get_trained_pokemon_by_id(pokemon_id)
        if pokemon:
            return jsonify(pokemon)
        else:
            return jsonify({"error": "Pokemon not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@trained_pokemon_bp.route('', methods=['POST'])
def add_trained_pokemon():
    """新しい育成済みポケモンを登録する"""
    data = request.json
    try:
        with DatabaseManager() as db:
            new_id = db.add_trained_pokemon(data)
        return jsonify({"id": new_id, "message": "Pokemon added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@trained_pokemon_bp.route('/<int:pokemon_id>', methods=['PUT'])
def update_trained_pokemon(pokemon_id):
    """育成済みポケモン情報を更新する"""
    data = request.json
    try:
        with DatabaseManager() as db:
            updated_rows = db.update_trained_pokemon(pokemon_id, data)
        if updated_rows > 0:
            return jsonify({"message": f"Pokemon {pokemon_id} updated successfully"})
        else:
            return jsonify({"error": "Pokemon not found or data unchanged"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@trained_pokemon_bp.route('/<int:pokemon_id>', methods=['DELETE'])
def delete_trained_pokemon(pokemon_id):
    """育成済みポケモンを削除する"""
    try:
        with DatabaseManager() as db:
            deleted_rows = db.delete_trained_pokemon(pokemon_id)
        if deleted_rows > 0:
            return jsonify({"message": f"Pokemon {pokemon_id} deleted successfully"})
        else:
            return jsonify({"error": "Pokemon not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
