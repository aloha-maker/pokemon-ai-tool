# src/services/trained_pokemon_service.py
from typing import List, Dict, Any
import time
from src.database.manager import DatabaseManager
from src.extensions import db
from src.models.trained_pokemon_moedl import TrainedPokemonModel
from src.models.natures_model import NatureModel
from src.models.type_model import TypeModel
from src.models.item_model import ItemModel
from src.models.abilities_model import AbilityModel

class TrainedPokemonService:
    """育成済みポケモンに関するビジネスロジックを担当する"""

    def get_all(self) -> List[Dict[str, Any]]:
        """すべての育成済みポケモンを取得する"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            # 技関連のJOINは一覧では不要なため削除し、クエリを安定させる
            query = """
                SELECT
                    tp.id,
                    tp.nickname,
                    tp.level,
                    p.name_ja as pokemon_name,
                    p.type1 as pokemon_type1,
                    p.type2 as pokemon_type2,
                    t.name_ja as tera_type_name,
                    a.name_ja as ability_name,
                    n.name_ja as nature_name,
                    i.name_ja as item_name
                FROM
                    trained_pokemons tp
                LEFT JOIN pokemons p ON tp.pokemon_id = p.id
                LEFT JOIN types t ON tp.tera_type_id = t.id
                LEFT JOIN abilities a ON tp.ability_id = a.id
                LEFT JOIN natures n ON tp.nature_id = n.id
                LEFT JOIN items i ON tp.held_item_id = i.id
                ORDER BY tp.updated_at DESC
            """
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, pokemon_id: int) -> Dict[str, Any] | None:
        """IDで単一の育成済みポケモンを取得する"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            # trained_pokemons から基本情報を取得
            cursor.execute("SELECT * FROM trained_pokemons WHERE id = ?", (pokemon_id,))
            row = cursor.fetchone()
            if not row:
                return None
            pokemon_data = dict(row)

            # pokemons テーブルから追加情報を取得
            cursor.execute(
                "SELECT name_ja, type1, type2 FROM pokemons WHERE id = ?", 
                (pokemon_data['pokemon_id'],)
            )
            pokemon_master_data = cursor.fetchone()
            if pokemon_master_data:
                # フロントエンドが期待するキー 'pokemon_name' と、シミュレーションに必要なタイプ情報を追加
                pokemon_data['pokemon_name'] = pokemon_master_data['name_ja']
                pokemon_data['type1'] = pokemon_master_data['type1']
                pokemon_data['type2'] = pokemon_master_data['type2']

            # 持ち物名を取得
            if pokemon_data.get('held_item_id'):
                cursor.execute(
                    "SELECT name_ja FROM items WHERE id = ?",
                    (pokemon_data['held_item_id'],)
                )
                item_row = cursor.fetchone()
                if item_row:
                    pokemon_data['item_name'] = item_row['name_ja']

            # 技情報を取得
            move_ids = [
                pokemon_data.get('move1_id'),
                pokemon_data.get('move2_id'),
                pokemon_data.get('move3_id'),
                pokemon_data.get('move4_id')
            ]
            
            moves_details = []
            for move_id in move_ids:
                if move_id:
                    # 技のシミュレーションに必要な情報をすべて取得
                    cursor.execute("SELECT id, name, type, category, power, accuracy FROM moves WHERE id = ?", (move_id,))
                    move_row = cursor.fetchone()
                    if move_row:
                        moves_details.append(dict(move_row))
            
            pokemon_data['moves'] = moves_details
            
            return pokemon_data

    def create(self, data: Dict[str, Any]) -> int:
        """新しい育成済みポケモンを作成する"""
        # TODO: Pydantic等によるデータバリデーションをここで行う
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            try:
                # dataに値がない場合は登録対象から除外する
                insert_data = {k: v for k, v in data.items() if v is not None and v != '' and k != 'id'}
                columns = list(insert_data.keys())
                placeholders = ', '.join('?' for _ in columns)
                values = list(insert_data.values())
                
                query = f"""
                    INSERT INTO trained_pokemons ({', '.join(columns)})
                    VALUES ({placeholders})
                """
                cursor.execute(query, values)
                db.conn.commit()
                return cursor.lastrowid
            except Exception as e:
                db.conn.rollback()
                raise e

    def update(self, pokemon_id: int, data: Dict[str, Any]) -> int:
        """育成済みポケモンを更新する"""
        # TODO: Pydantic等によるデータバリデーションをここで行う
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            # 'id'キーを削除し、updated_atを更新
            data.pop('id', None)
            data['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

            try:
                # dataに値がない場合は更新対象から除外する
                update_data = {k: v for k, v in data.items() if v is not None and v != ''}
                if not update_data:
                    return 0 # 更新対象がない

                set_clauses = [f"{col} = ?" for col in update_data.keys()]
                values = list(update_data.values())
                values.append(pokemon_id)

                query = f"""
                    UPDATE trained_pokemons
                    SET {', '.join(set_clauses)}
                    WHERE id = ?
                """
                cursor.execute(query, values)
                db.conn.commit()
                return cursor.rowcount
            except Exception as e:
                db.conn.rollback()
                raise e

    def delete(self, id: int) -> int:
        """育成済みポケモンを削除する"""
        try:
            model = TrainedPokemonModel.query.get(id)
            print(model)
            if model:
                db.session.delete(model)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            raise e
        # with DatabaseManager() as db:
        #     cursor = db.get_cursor()
        #     cursor.execute("DELETE FROM trained_pokemons WHERE id = ?", (pokemon_id,))
        #     db.conn.commit()
        #     return cursor.rowcount
