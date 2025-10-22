# src/services/trained_pokemon_service.py
from typing import List, Dict, Any
from src.database.manager import DatabaseManager

class TrainedPokemonService:
    """育成済みポケモンに関するビジネスロジックを担当する"""

    def get_all(self) -> List[Dict[str, Any]]:
        """すべての育成済みポケモンを取得する"""
        with DatabaseManager() as db:
            return db.get_all_trained_pokemons()

    def get_by_id(self, pokemon_id: int) -> Dict[str, Any] | None:
        """IDで単一の育成済みポケモンを取得する"""
        with DatabaseManager() as db:
            return db.get_trained_pokemon_by_id(pokemon_id)

    def create(self, data: Dict[str, Any]) -> int:
        """新しい育成済みポケモンを作成する"""
        # TODO: Pydantic等によるデータバリデーションをここで行う
        with DatabaseManager() as db:
            return db.add_trained_pokemon(data)

    def update(self, pokemon_id: int, data: Dict[str, Any]) -> int:
        """育成済みポケモンを更新する"""
        # TODO: Pydantic等によるデータバリデーションをここで行う
        with DatabaseManager() as db:
            return db.update_trained_pokemon(pokemon_id, data)

    def delete(self, pokemon_id: int) -> int:
        """育成済みポケモンを削除する"""
        with DatabaseManager() as db:
            return db.delete_trained_pokemon(pokemon_id)
