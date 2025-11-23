# src/routes/api/master.py
import logging
from flask import Blueprint
from src.services.master_data_service import MasterDataService
from src.utils.response_handler import api_success, api_fail, api_error

# BlueprintのURLプレフィックスを/apiに設定
master_bp = Blueprint('master_api', __name__, url_prefix='/api')
service = MasterDataService()

@master_bp.route('/master/<string:resource_name>', methods=['GET'])
def get_master_data_generic(resource_name):
    """汎用的なマスターデータ取得エンドポイント"""
    try:
        # 意図しないリソースへのアクセスを防ぐためのホワイトリスト
        allowed_resources = ['pokemons', 'types', 'items', 'natures', 'moves', 'abilities']
        if resource_name not in allowed_resources:
            return api_fail({"error": f"リソース '{resource_name}' は見つかりません。"}, 404)
        
        data = service.get_master_data_by_resource(resource_name)
        
        # データが取得できなかった場合のハンドリング
        if data is None:
            return api_fail({"error": f"リソース '{resource_name}' のデータ取得に失敗しました。"}, 404)
            
        return api_success({resource_name: data})
    except Exception as e:
        logging.exception(f"マスターデータ({resource_name})の取得中に予期せぬエラーが発生しました: {e}")
        return api_error("サーバー内部でエラーが発生しました。")

@master_bp.route('/pokemon/<int:pokemon_id>/abilities', methods=['GET'])
def get_pokemon_abilities(pokemon_id):
    """ポケモンの特性取得API"""
    try:
        abilities = service.get_abilities_by_pokemon_id(pokemon_id)
        
        if abilities is None:
            return api_fail({"error": f"ポケモンID '{pokemon_id}' が見つからないか、特性がありません。"}, 404)
        return api_success({"abilities": abilities})
    except Exception as e:
        logging.exception(f"ポケモン(ID:{pokemon_id})の特性情報取得中に予期せぬエラーが発生しました: {e}")
        return api_error("サーバー内部でエラーが発生しました。")

@master_bp.route('/pokemon/<int:pokemon_id>/moves', methods=['GET'])
def get_pokemon_moves(pokemon_id):
    """ポケモンの技取得API"""
    try:
        moves = service.get_moves_by_pokemon_id(pokemon_id)
        if moves is None:
            return api_fail({"error": f"ポケモンID '{pokemon_id}' が見つからないか、技がありません。"}, 404)
        return api_success({"moves": moves})
    except Exception as e:
        logging.exception(f"ポケモン(ID:{pokemon_id})の技情報取得中に予期せぬエラーが発生しました: {e}")
        return api_error("サーバー内部でエラーが発生しました。")
