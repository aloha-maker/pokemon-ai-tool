# src/services/party_service.py
from typing import List, Dict, Any
import time
from src.database.manager import DatabaseManager
from src.extensions import db

from src.schemas.pokemon_battle import Party
from src.schemas.pokemon_battle import Pokemon

from src.schemas.pokemon_battle.party import Party
from src.models.party_model import PartyModel
from src.models.partyMember_model import PartyMemberModel

class PartyService:
    """パーティに関するビジネスロジックを担当する"""

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
        try:
            party = PartyModel(
                name=data['name'],
                description=data.get('description', '')
            )
            db.session.add(party)
            db.session.flush()

            members = data.get('members', [])
            if members:
                for index, member_id in enumerate(members):
                    membar = PartyMemberModel(
                        party_id=party.id,
                        trained_pokemon_id=member_id,
                        member_index=index
                    )
                    db.session.add(membar)
            
            db.session.commit()

            return party.id  # 作成したIDを返す

        except Exception as e:
            db.session.rollback()
            raise e
        # with DatabaseManager() as db:
        #     cursor = db.get_cursor()
        #     try:
        #         cursor.execute(
        #             "INSERT INTO parties (name, description) VALUES (?, ?)",
        #             (data['name'], data.get('description', ''))
        #         )
        #         party_id = cursor.lastrowid
                
        #         members = data.get('members', [])
        #         if members:
        #             member_values = [
        #                 (party_id, member_id, index)
        #                 for index, member_id in enumerate(members)
        #                 if member_id is not None
        #             ]
        #             cursor.executemany(
        #                 "INSERT INTO party_members (party_id, trained_pokemon_id, member_index) VALUES (?, ?, ?)",
        #                 member_values
        #             )
                
        #         db.conn.commit()
        #         return party_id
        #     except Exception as e:
        #         db.conn.rollback()
        #         raise e

    def update(self, party_id: int, data: Dict[str, Any]) -> int:
        """パーティを更新する"""
        try:
            party = PartyModel.query.get(party_id)
            if not party:
                return False
            PartyModel.query.filter_by(id=party_id).update({
                "name": data["name"],
                "description": data.get("description")
            })
            # メンバー情報を更新            
            for index, member in enumerate(data["members"]):
                PartyMemberModel.query.filter_by(party_id=party_id,member_index=index).update({
                    "trained_pokemon_id": member,
                })
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self, party_id: int) -> int:
        """パーティを削除する"""
        try:
            model = PartyModel.query.get(party_id)
            if model:
                db.session.delete(model)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
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

    def get_party_menber_by_id(self, party_id: int):
        party = Party.load_from_db(party_id)
        
        return party.to_dict()
        
