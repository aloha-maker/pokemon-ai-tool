# src/services/party_service.py
from typing import List, Dict, Any
from src.database.manager import DatabaseManager

class PartyService:
    """パーティに関するビジネスロジックを担当する"""

    def get_all(self) -> List[Dict[str, Any]]:
        """すべてのパーティを取得する"""
        with DatabaseManager() as db:
            return db.get_all_parties()

    def get_by_id(self, party_id: int) -> Dict[str, Any] | None:
        """IDで単一のパーティを取得する"""
        with DatabaseManager() as db:
            return db.get_party_by_id(party_id)

    def create(self, data: Dict[str, Any]) -> int:
        """新しいパーティを作成する"""
        with DatabaseManager() as db:
            return db.add_party(data)

    def update(self, party_id: int, data: Dict[str, Any]) -> int:
        """パーティを更新する"""
        with DatabaseManager() as db:
            return db.update_party(party_id, data)

    def delete(self, party_id: int) -> int:
        """パーティを削除する"""
        with DatabaseManager() as db:
            return db.delete_party(party_id)

    def register_generated_party(self, party_data: List[Dict[str, Any]], party_name: str) -> None:
        """AIが生成したパーティを育成済みポケモンとパーティの両方に登録する"""
        if not party_data or not party_name or len(party_data) != 6:
            raise ValueError("Invalid party data provided. Party must contain 6 Pokemon and a name.")

        with DatabaseManager() as db:
            new_pokemon_ids = []
            for p in party_data:
                # add_trained_pokemon が受け取る形式にデータを整形
                trained_pokemon_data = {
                    "pokemon_id": p.get('pokemon_id'),
                    "nickname": p.get('name', 'Unknown'), # ニックネームはとりあえずポケモン名
                    "level": 50,
                    "tera_type_id": p.get('tera_type_id'),
                    "ability_id": p.get('ability_id'),
                    "nature_id": p.get('nature_id'),
                    "held_item_id": p.get('item_id'),
                    "move1_id": p['moves'][0]['id'] if len(p.get('moves', [])) > 0 else None,
                    "move2_id": p['moves'][1]['id'] if len(p.get('moves', [])) > 1 else None,
                    "move3_id": p['moves'][2]['id'] if len(p.get('moves', [])) > 2 else None,
                    "move4_id": p['moves'][3]['id'] if len(p.get('moves', [])) > 3 else None,
                    **p.get('evs', {}) # ev_hp, ev_atk, ... を展開して渡す
                }
                new_id = db.add_trained_pokemon(trained_pokemon_data)
                new_pokemon_ids.append(new_id)
            
            # 新しいパーティを登録
            party_to_add = {
                "name": party_name,
                "description": "AIにより自動生成されたパーティです。",
                "members": new_pokemon_ids
            }
            db.add_party(party_to_add)
