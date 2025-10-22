# src/services/master_data_service.py
from typing import List, Dict, Any
from src.database.manager import DatabaseManager

class MasterDataService:
    """マスターデータや汎用的なDB操作に関するビジネスロジックを担当する"""

    def get_master_data(self, resource_name: str) -> List[Dict[str, Any]]:
        """指定されたリソースのマスターデータを取得する"""
        with DatabaseManager() as db:
            return db.get_master_data_by_resource(resource_name)

    def get_abilities_for_pokemon(self, pokemon_id: int) -> List[Dict[str, Any]]:
        """特定のポケモンの特性リストを取得する"""
        with DatabaseManager() as db:
            return db.get_abilities_by_pokemon_id(pokemon_id)

    def get_moves_for_pokemon(self, pokemon_id: int) -> List[Dict[str, Any]]:
        """特定のポケモンの技リストを取得する"""
        with DatabaseManager() as db:
            return db.get_moves_by_pokemon_id(pokemon_id)

    def get_all_table_names(self) -> List[str]:
        """すべてのテーブル名を取得する"""
        with DatabaseManager() as db:
            return db.get_all_tables()

    def search_table(self, table_name: str, keyword: str, page: int, per_page: int) -> Dict[str, Any]:
        """指定されたテーブルを検索する"""
        if not table_name:
            raise ValueError("Table name is required")
        
        offset = (page - 1) * per_page
        with DatabaseManager() as db:
            # DBマネージャは不正なテーブル名に対してValueErrorを発生させる可能性がある
            return db.search_table(table_name, keyword, limit=per_page, offset=offset)
