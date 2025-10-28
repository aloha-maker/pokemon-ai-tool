# src/services/master_data_service.py
from typing import List, Dict, Any
from src.database.manager import DatabaseManager

class MasterDataService:
    """マスターデータに関するビジネスロジックを担当する"""

    def get_pokemon_by_name(self, name: str) -> dict | None:
        """ポケモン名から詳細データを取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT * FROM pokemons WHERE name_ja = ? OR name = ?", (name, name))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_move_by_name(self, name: str) -> dict | None:
        """技名から詳細データを取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            cursor.execute("SELECT * FROM moves WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_pokemons_by_names(self, names: list[str]) -> list[dict]:
        """複数のポケモン名から詳細データのリストを取得する。"""
        if not names:
            return []
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            placeholders = ', '.join('?' for _ in names)
            query = f"SELECT * FROM pokemons WHERE name_ja IN ({placeholders}) OR name IN ({placeholders})"
            params = names + names
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_master_data_by_resource(self, resource: str) -> list[dict]:
        """指定されたリソース（テーブル名）からUI表示用のマスターデータをすべて取得する。"""
        if resource not in ['items', 'natures', 'abilities', 'moves', 'types', 'pokemons']:
            raise ValueError(f"Invalid resource: {resource}")
        
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            if resource == 'pokemons':
                cursor.execute("SELECT MIN(id) as id, name, name_ja,speed FROM pokemons GROUP BY name_ja ORDER BY name_ja")
            elif resource == 'natures':
                cursor.execute(f"SELECT * FROM {resource} WHERE name_ja IS NOT NULL AND name_ja != '' ORDER BY name_ja")
            else:
                 cursor.execute(f"SELECT id, name, name_ja FROM {resource} WHERE name_ja IS NOT NULL AND name_ja != '' ORDER BY name_ja")
            return [dict(row) for row in cursor.fetchall()]

    def get_abilities_by_pokemon_id(self, pokemon_id: int) -> list[dict] | None:
        """
        指定されたポケモンIDが持つ特性を取得する。
        ポケモンが存在しない場合はNoneを返す。
        """
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            cursor.execute("SELECT abilities FROM pokemons WHERE id = ?", (pokemon_id,))
            row = cursor.fetchone()
            
            # ポケモンが存在しない場合
            if not row:
                return None
            
            # 特性情報がない場合
            if not row['abilities']:
                return []

            try:
                ability_ids = [int(id_str) for id_str in row['abilities'].split(',') if id_str.strip().isdigit()]
                if not ability_ids:
                    return []
            except (ValueError, AttributeError):
                return []

            placeholders = ', '.join('?' for _ in ability_ids)
            query = f"SELECT id, name, name_ja FROM abilities WHERE id IN ({placeholders})"
            
            cursor.execute(query, ability_ids)
            return [dict(row) for row in cursor.fetchall()]

    def get_moves_by_pokemon_id(self, pokemon_id: int) -> list[dict] | None:
        """
        指定されたポケモンIDが覚える技を取得する。
        ポケモンが存在しない場合はNoneを返す。
        """
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            cursor.execute("SELECT moves FROM pokemons WHERE id = ?", (pokemon_id,))
            row = cursor.fetchone()

            # ポケモンが存在しない場合
            if not row:
                return None

            # 技情報がない場合
            if not row['moves']:
                return []

            try:
                move_ids = [int(id_str) for id_str in row['moves'].split(',') if id_str.strip().isdigit()]
                if not move_ids:
                    return []
            except (ValueError, AttributeError):
                return []

            placeholders = ', '.join('?' for _ in move_ids)
            query = f"SELECT id, name, name_ja FROM moves WHERE id IN ({placeholders})"
            
            cursor.execute(query, move_ids)
            return [dict(row) for row in cursor.fetchall()]

    def get_moves_by_type(self, move_type: str, category: str, limit: int = 10) -> list[dict]:
        """指定されたタイプとカテゴリの技を取得する（威力順）。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            query = """
                SELECT *
                FROM moves
                WHERE type = ? AND category = ? AND power > 0
                ORDER BY power DESC
                LIMIT ?
            """
            cursor.execute(query, (move_type, category, limit))
            return [dict(row) for row in cursor.fetchall()]