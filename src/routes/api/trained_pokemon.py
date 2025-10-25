# src/routes/api/trained_pokemon.py
from flask import Blueprint, request
from src.services.trained_pokemon_service import TrainedPokemonService
from src.utils.response_handler import api_success, api_fail, api_error
import logging

trained_pokemon_bp = Blueprint('trained_pokemon_api', __name__, url_prefix='/api/trained-pokemons')
service = TrainedPokemonService()

@trained_pokemon_bp.route('', methods=['GET'])
def get_trained_pokemons():
    """育成済みポケモンの一覧を取得する"""
    try:
        pokemons = service.get_all()
        return api_success(pokemons)
    except Exception as e:
        logging.exception("Error getting all trained pokemons")
        return api_error("育成済みポケモン一覧の取得に失敗しました。")

@trained_pokemon_bp.route('/<int:pokemon_id>', methods=['GET'])
def get_trained_pokemon(pokemon_id):
    """単一の育成済みポケモン情報を取得する"""
    try:
        pokemon = service.get_by_id(pokemon_id)
        if pokemon:
            return api_success(pokemon)
        else:
            return api_fail({"message": "Pokemon not found"}, 404)
    except Exception as e:
        logging.exception(f"Error getting trained pokemon {pokemon_id}")
        return api_error("育成済みポケモン情報の取得に失敗しました。")

@trained_pokemon_bp.route('', methods=['POST'])
def add_trained_pokemon():
    """新しい育成済みポケモンを登録する"""
    try:
        data = request.json
        if not data:
            return api_fail({"message": "No data provided"})
        
        new_id = service.create(data)
        return api_success({"id": new_id, "message": "Pokemon added successfully"}, 201)
    except Exception as e:
        logging.exception("Error adding trained pokemon")
        return api_error("育成済みポケモンの登録に失敗しました。")

@trained_pokemon_bp.route('/<int:pokemon_id>', methods=['PUT'])
def update_trained_pokemon(pokemon_id):
    """育成済みポケモン情報を更新する"""
    try:
        data = request.json
        if not data:
            return api_fail({"message": "No data provided"})

        updated_rows = service.update(pokemon_id, data)
        if updated_rows > 0:
            return api_success({"message": f"Pokemon {pokemon_id} updated successfully"})
        else:
            return api_fail({"message": "Pokemon not found or data unchanged"}, 404)
    except Exception as e:
        logging.exception(f"Error updating trained pokemon {pokemon_id}")
        return api_error("育成済みポケモンの更新に失敗しました。")

@trained_pokemon_bp.route('/<int:pokemon_id>', methods=['DELETE'])
def delete_trained_pokemon(pokemon_id):
    """育成済みポケモンを削除する"""
    try:
        deleted_rows = service.delete(pokemon_id)
        if deleted_rows > 0:
            return api_success({"message": f"Pokemon {pokemon_id} deleted successfully"})
        else:
            return api_fail({"message": "Pokemon not found"}, 404)
    except Exception as e:
        logging.exception(f"Error deleting trained pokemon {pokemon_id}")
        return api_error("育成済みポケモンの削除に失敗しました。")
