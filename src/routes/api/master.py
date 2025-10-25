# src/routes/api/master.py
from flask import Blueprint, jsonify
from src.services.master_data_service import MasterDataService

master_bp = Blueprint('master_api', __name__)
service = MasterDataService()

@master_bp.route('/api/master/<string:resource_name>', methods=['GET'])
def get_master_data_generic(resource_name):
    """汎用的なマスターデータ取得エンドポイント"""
    # 意図しないリソースへのアクセスを防ぐためのホワイトリスト
    allowed_resources = ['pokemons', 'types', 'items', 'natures', 'moves', 'abilities']
    if resource_name not in allowed_resources:
        return jsonify({"error": "Resource not found"}), 404
    
    data = service.get_master_data_by_resource(resource_name)
    return jsonify(data)

@master_bp.route('/api/pokemon/<int:pokemon_id>/abilities', methods=['GET'])
def get_pokemon_abilities(pokemon_id):
    abilities = service.get_abilities_by_pokemon_id(pokemon_id)
    return jsonify(abilities)

@master_bp.route('/api/pokemon/<int:pokemon_id>/moves', methods=['GET'])
def get_pokemon_moves(pokemon_id):
    moves = service.get_moves_by_pokemon_id(pokemon_id)
    return jsonify(moves)
