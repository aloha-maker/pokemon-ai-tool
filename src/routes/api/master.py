# src/routes/api/master.py
from flask import Blueprint, jsonify
from src.database.manager import DatabaseManager

master_bp = Blueprint('master_api', __name__)

# 各マスターデータを取得するための汎用関数
def get_master_data(resource_name):
    with DatabaseManager() as db:
        data = db.get_master_data_by_resource(resource_name)
    return jsonify(data)

@master_bp.route('/api/master/pokemons', methods=['GET'])
def get_pokemons():
    return get_master_data('pokemons')

@master_bp.route('/api/master/types', methods=['GET'])
def get_types():
    return get_master_data('types')

@master_bp.route('/api/master/items', methods=['GET'])
def get_items():
    return get_master_data('items')

@master_bp.route('/api/master/natures', methods=['GET'])
def get_natures():
    return get_master_data('natures')

@master_bp.route('/api/master/moves', methods=['GET'])
def get_moves():
    return get_master_data('moves')

@master_bp.route('/api/master/abilities', methods=['GET'])
def get_abilities():
    return get_master_data('abilities')

@master_bp.route('/api/pokemon/<int:pokemon_id>/abilities', methods=['GET'])
def get_pokemon_abilities(pokemon_id):
    with DatabaseManager() as db:
        abilities = db.get_abilities_by_pokemon_id(pokemon_id)
    return jsonify(abilities)

@master_bp.route('/api/pokemon/<int:pokemon_id>/moves', methods=['GET'])
def get_pokemon_moves(pokemon_id):
    with DatabaseManager() as db:
        moves = db.get_moves_by_pokemon_id(pokemon_id)
    return jsonify(moves)
