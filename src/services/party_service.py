# src/services/party_service.py
from typing import List, Dict, Any
import time
from src.database.manager import DatabaseManager
from src.services.trained_pokemon_service import TrainedPokemonService

class PartyService:
    """パーティに関するビジネスロジックを担当する"""

    def __init__(self, trained_pokemon_service: TrainedPokemonService = None):
        self.trained_pokemon_service = trained_pokemon_service or TrainedPokemonService()

    def get_all(self) -> List[Dict[str, Any]]:
        """すべてのパーティを、メンバー情報を含めて取得する"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            query = """
                SELECT
                    p.id as party_id,
                    p.name as party_name,
                    p.description as party_description,
                    p.created_at as party_created_at,
                    p.updated_at as party_updated_at,
                    tp.id as member_id,
                    tp.nickname,
                    tp.level,
                    pk.name_ja as pokemon_name,
                    pk.type1 as pokemon_type1,
                    pk.type2 as pokemon_type2,
                    i.name_ja as item_name
                FROM
                    parties p
                LEFT JOIN party_members pm ON p.id = pm.party_id
                LEFT JOIN trained_pokemons tp ON pm.trained_pokemon_id = tp.id
                LEFT JOIN pokemons pk ON tp.pokemon_id = pk.id
                LEFT JOIN items i ON tp.held_item_id = i.id
                ORDER BY p.updated_at DESC, pm.member_index ASC
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            parties_dict = {}
            for row in rows:
                party_id = row['party_id']
                if party_id not in parties_dict:
                    parties_dict[party_id] = {
                        'id': party_id,
                        'name': row['party_name'],
                        'description': row['party_description'],
                        'created_at': row['party_created_at'],
                        'updated_at': row['party_updated_at'],
                        'members': []
                    }
                
                if row['member_id'] is not None:
                    parties_dict[party_id]['members'].append({
                        'id': row['member_id'],
                        'nickname': row['nickname'],
                        'level': row['level'],
                        'pokemon_name': row['pokemon_name'],
                        'pokemon_type1': row['pokemon_type1'],
                        'pokemon_type2': row['pokemon_type2'],
                        'item_name': row['item_name']
                    })

            return list(parties_dict.values())

    def get_by_id(self, party_id: int) -> Dict[str, Any] | None:
        """IDで指定したパーティの情報を、メンバーと技詳細を含めて効率的に取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            cursor.execute("SELECT * FROM parties WHERE id = ?", (party_id,))
            party_row = cursor.fetchone()
            if not party_row:
                return None
            
            party_dict = dict(party_row)
            
            members_query = """
                SELECT
                    tp.*,
                    pm.member_index,
                    p.name_ja as pokemon_name,
                    i.name_ja as item_name
                FROM party_members pm
                JOIN trained_pokemons tp ON pm.trained_pokemon_id = tp.id
                LEFT JOIN pokemons p ON tp.pokemon_id = p.id
                LEFT JOIN items i ON tp.held_item_id = i.id
                WHERE pm.party_id = ?
                ORDER BY pm.member_index ASC
            """
            cursor.execute(members_query, (party_id,))
            member_rows = cursor.fetchall()
            
            if not member_rows:
                party_dict['members'] = []
                return party_dict

            all_move_ids = set()
            for member in member_rows:
                for i in range(1, 5):
                    move_id = member[f'move{i}_id']
                    if move_id:
                        all_move_ids.add(move_id)
            
            moves_details_map = {}
            if all_move_ids:
                placeholders = ', '.join('?' for _ in all_move_ids)
                moves_query = f"SELECT * FROM moves WHERE id IN ({placeholders})"
                cursor.execute(moves_query, list(all_move_ids))
                for move_row in cursor.fetchall():
                    moves_details_map[move_row['id']] = dict(move_row)

            members_list = []
            for member_row in member_rows:
                member_data = dict(member_row)
                member_data['moves'] = []
                for i in range(1, 5):
                    move_id = member_data.get(f'move{i}_id')
                    if move_id and move_id in moves_details_map:
                        member_data['moves'].append(moves_details_map[move_id])
                members_list.append(member_data)

            party_dict['members'] = members_list
            return party_dict

    def create(self, data: Dict[str, Any]) -> int:
        """新しいパーティを作成する"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            try:
                cursor.execute(
                    "INSERT INTO parties (name, description) VALUES (?, ?)",
                    (data['name'], data.get('description', ''))
                )
                party_id = cursor.lastrowid
                
                members = data.get('members', [])
                if members:
                    member_values = [
                        (party_id, member_id, index)
                        for index, member_id in enumerate(members)
                        if member_id is not None
                    ]
                    cursor.executemany(
                        "INSERT INTO party_members (party_id, trained_pokemon_id, member_index) VALUES (?, ?, ?)",
                        member_values
                    )
                
                db.conn.commit()
                return party_id
            except Exception as e:
                db.conn.rollback()
                raise e

    def update(self, party_id: int, data: Dict[str, Any]) -> int:
        """パーティを更新する"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            try:
                cursor.execute(
                    "UPDATE parties SET name = ?, description = ?, updated_at = ? WHERE id = ?",
                    (data['name'], data.get('description', ''), time.strftime('%Y-%m-%d %H:%M:%S'), party_id)
                )
                update_rowcount = cursor.rowcount # UPDATEの結果を保存
                
                cursor.execute("DELETE FROM party_members WHERE party_id = ?", (party_id,))
                
                members = data.get('members', [])
                if members:
                    member_values = [
                        (party_id, member_id, index)
                        for index, member_id in enumerate(members)
                        if member_id is not None
                    ]
                    cursor.executemany(
                        "INSERT INTO party_members (party_id, trained_pokemon_id, member_index) VALUES (?, ?, ?)",
                        member_values
                    )
                
                db.conn.commit()
                return update_rowcount # 保存した値を返す
            except Exception as e:
                db.conn.rollback()
                raise e

    def delete(self, party_id: int) -> int:
        """パーティを削除する"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            try:
                cursor.execute("DELETE FROM parties WHERE id = ?", (party_id,))
                db.conn.commit()
                return cursor.rowcount
            except Exception as e:
                db.conn.rollback()
                raise e

    def get_pokemon_names(self, party_id: int) -> List[str]:
        """指定されたパーティIDのポケモンの名前（日本語）のリストを取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            query = """
                SELECT p.name_ja
                FROM party_members pm
                JOIN trained_pokemons tp ON pm.trained_pokemon_id = tp.id
                JOIN pokemons p ON tp.pokemon_id = p.id
                WHERE pm.party_id = ?
                ORDER BY pm.member_index
            """
            cursor.execute(query, (party_id,))
            rows = cursor.fetchall()
            return [row['name_ja'] for row in rows]

    def register_generated_party(self, party_data: List[Dict[str, Any]], party_name: str) -> None:
        """AIが生成したパーティを育成済みポケモンとパーティの両方に登録する"""
        if not party_data or not party_name or len(party_data) != 6:
            raise ValueError("Invalid party data provided. Party must contain 6 Pokemon and a name.")

        new_pokemon_ids = []
        
        for p in party_data:
            trained_pokemon_data = {
                "pokemon_id": p.get('pokemon_id'),
                "nickname": p.get('name', 'Unknown'),
                "level": 50,
                "tera_type_id": p.get('tera_type_id'),
                "ability_id": p.get('ability_id'),
                "nature_id": p.get('nature_id'),
                "held_item_id": p.get('item_id'),
                "move1_id": p['moves'][0]['id'] if len(p.get('moves', [])) > 0 else None,
                "move2_id": p['moves'][1]['id'] if len(p.get('moves', [])) > 1 else None,
                "move3_id": p['moves'][2]['id'] if len(p.get('moves', [])) > 2 else None,
                "move4_id": p['moves'][3]['id'] if len(p.get('moves', [])) > 3 else None,
                **p.get('evs', {})
            }
            new_id = self.trained_pokemon_service.create(trained_pokemon_data)
            new_pokemon_ids.append(new_id)
        
        party_to_add = {
            "name": party_name,
            "description": "AIにより自動生成されたパーティです。",
            "members": new_pokemon_ids
        }
        self.create(party_to_add)
