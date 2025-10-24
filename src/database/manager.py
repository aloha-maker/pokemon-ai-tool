import sqlite3
import os
import json
import time

class DatabaseManager:
    """
    データベースへの接続と操作を管理するクラス。
    アプリケーションの他モジュールは、このクラスを通じてデータベースにアクセスする。
    """
    def __init__(self, db_path=None, conn=None):
        """
        DatabaseManagerを初期化する。
        connが指定された場合はその接続を使用する。
        db_pathが指定されない場合、プロジェクトルートからの相対パスを使用する。
        """
        from flask import current_app

        self.conn = conn
        self._external_conn = conn is not None

        if not self._external_conn:
            if db_path is None:
                # Flaskアプリケーションコンテキストからデータベースパスを取得
                db_url = current_app.config.get('DATABASE_URL')
                if db_url and db_url.startswith('sqlite:///'):
                    self.db_path = db_url.replace('sqlite:///', '')
                else:
                    # フォールバックとして従来のパス構築を使用
                    self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'pokemon_ai.db')
            else:
                self.db_path = db_path

    def __enter__(self):
        """コンテキストマネージャの開始時にデータベースに接続する。"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャの終了時にデータベース接続を閉じる。"""
        self.close()

    def connect(self):
        """データベースに接続する。"""
        if self._external_conn:
            return
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                print(f"Error connecting to database: {e}")
                raise

    def close(self):
        """データベース接続を閉じる。外部から注入された接続は閉じない。"""
        if self._external_conn:
            return
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_cursor(self):
        """
        接続からカーソルを取得する。
        接続が存在しない場合は、まず接続を試みる。
        """
        self.connect()
        return self.conn.cursor()

    def get_pokemon_by_name(self, name: str) -> dict | None:
        """ポケモン名から詳細データを取得する。"""
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM pokemons WHERE name_ja = ? OR name = ?", (name, name))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_move_by_name(self, name: str) -> dict | None:
        """技名から詳細データを取得する。"""
        cursor = self.get_cursor()
        # 完全一致または前方一致で検索（例：「１０まんばりき」）
        cursor.execute("SELECT * FROM moves WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def prepare_battle_log(self, my_party_id: int, opponent_party: list[str]) -> int:
        """
        対戦前のパーティ情報で `battle_logs` テーブルにレコードを作成する。
        resultは'unknown'で登録される。
        戻り値は追加されたレコードのID。
        """
        cursor = self.get_cursor()
        try:
            cursor.execute(
                "INSERT INTO battle_logs (my_party_id, opponent_party, result) VALUES (?, ?, ?)",
                (
                    my_party_id,
                    json.dumps(opponent_party, ensure_ascii=False),
                    'unknown'
                )
            )
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_pokemons_by_names(self, names: list[str]) -> list[dict]:
        """複数のポケモン名から詳細データのリストを取得する。"""
        if not names:
            return []
        cursor = self.get_cursor()
        placeholders = ', '.join('?' for _ in names)
        query = f"SELECT * FROM pokemons WHERE name_ja IN ({placeholders}) OR name IN ({placeholders})"
        # name_jaとnameの両方で検索するため、リストを2回渡す
        params = names + names
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # --- F-05: 育成済みポケモン管理 (Trained Pokemons) ---

    # --- F-06: パーティ管理 (Parties) ---

    def get_all_parties(self) -> list[dict]:
        """登録済みのすべてのパーティを、JOINを使用して効率的に取得する。"""
        cursor = self.get_cursor()
        
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
            
            # メンバーが存在する場合のみ追加
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

    def get_party_by_id(self, party_id: int) -> dict | None:
        """IDで指定したパーティの情報を、メンバーと技詳細を含めて効率的に取得する。"""
        cursor = self.get_cursor()
        
        # 1. パーティの基本情報を取得
        cursor.execute("SELECT * FROM parties WHERE id = ?", (party_id,))
        party_row = cursor.fetchone()
        if not party_row:
            return None
        
        party_dict = dict(party_row)
        
        # 2. パーティメンバーの基本情報と技IDを一括で取得
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

        # 3. 取得した全メンバーから、すべての技IDを収集
        all_move_ids = set()
        for member in member_rows:
            for i in range(1, 5):
                move_id = member[f'move{i}_id']
                if move_id:
                    all_move_ids.add(move_id)
        
        # 4. 全技詳細を一括で取得
        moves_details_map = {}
        if all_move_ids:
            placeholders = ', '.join('?' for _ in all_move_ids)
            moves_query = f"SELECT * FROM moves WHERE id IN ({placeholders})"
            cursor.execute(moves_query, list(all_move_ids))
            for move_row in cursor.fetchall():
                moves_details_map[move_row['id']] = dict(move_row)

        # 5. メンバー情報に技詳細リストを 'moves' キーとして追加
        members_list = []
        for member_row in member_rows:
            member_data = dict(member_row)
            member_data['moves'] = [] # Create the 'moves' key
            for i in range(1, 5):
                move_id = member_data.get(f'move{i}_id')
                if move_id and move_id in moves_details_map:
                    member_data['moves'].append(moves_details_map[move_id])
            members_list.append(member_data)

        party_dict['members'] = members_list
        return party_dict



    def add_party(self, data: dict) -> int:
        """新しいパーティをデータベースに登録する。"""
        cursor = self.get_cursor()
        
        try:
            # パーティ名を登録
            cursor.execute(
                "INSERT INTO parties (name, description) VALUES (?, ?)",
                (data['name'], data.get('description', ''))
            )
            party_id = cursor.lastrowid
            
            # パーティメンバーを登録
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
            
            self.conn.commit()
            return party_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def update_party(self, party_id: int, data: dict) -> int:
        """指定したIDのパーティ情報を更新する。"""
        cursor = self.get_cursor()
        
        try:
            # パーティ名と説明を更新
            cursor.execute(
                "UPDATE parties SET name = ?, description = ?, updated_at = ? WHERE id = ?",
                (data['name'], data.get('description', ''), time.strftime('%Y-%m-%d %H:%M:%S'), party_id)
            )
            
            # 既存のメンバーを一旦削除
            cursor.execute("DELETE FROM party_members WHERE party_id = ?", (party_id,))
            
            # 新しいメンバーを登録
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
            
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_party(self, party_id: int) -> int:
        """指定したIDのパーティを削除する。ON DELETE CASCADEによりメンバーも削除される。"""
        cursor = self.get_cursor()
        try:
            cursor.execute("DELETE FROM parties WHERE id = ?", (party_id,))
            self.conn.commit()
            return cursor.rowcount
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_party_pokemon_names(self, party_id: int) -> list[str]:
        """指定されたパーティIDのポケモンの名前（日本語）のリストを取得する。"""
        cursor = self.get_cursor()
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

    def get_master_data_by_resource(self, resource: str) -> list[dict]:
        """指定されたリソース（テーブル名）からマスターデータをすべて取得する。"""
        if resource not in ['items', 'natures', 'abilities', 'moves', 'types', 'pokemons']:
            raise ValueError(f"Invalid resource: {resource}")
        
        cursor = self.get_cursor()
        # pokemonsテーブルはname_jaでソート
        order_column = 'name_ja' if resource == 'pokemons' else 'name'
        cursor.execute(f"SELECT * FROM {resource} ORDER BY {order_column}")
        return [dict(row) for row in cursor.fetchall()]

    def get_all_tables(self) -> list[str]:
        """データベース内のすべてのテーブル名を取得する。"""
        cursor = self.get_cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        return [row['name'] for row in cursor.fetchall()]

    def search_table(self, table_name: str, keyword: str = '', limit: int = 50, offset: int = 0) -> dict:
        """
        指定されたテーブルを検索し、結果と総数を返す。
        """
        # テーブル名のホワイトリストチェック
        cursor = self.get_cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        allowed_tables = [row['name'] for row in cursor.fetchall()]
        if table_name not in allowed_tables:
            raise ValueError(f"Invalid table name: {table_name}")

        # カラム名を取得
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row['name'] for row in cursor.fetchall()]

        # WHERE句を構築
        where_clauses = []
        params = []
        if keyword:
            for column in columns:
                where_clauses.append(f"CAST({column} AS TEXT) LIKE ?")
                params.append(f"%{keyword}%")
        
        where_sql = f"WHERE {' OR '.join(where_clauses)}" if where_clauses else ""

        # 総件数を取得するクエリ
        count_query = f"SELECT COUNT(*) as total FROM {table_name} {where_sql}"
        cursor.execute(count_query, params)
        total_records = cursor.fetchone()['total']

        # データを取得するクエリ
        data_query = f"SELECT * FROM {table_name} {where_sql} LIMIT ? OFFSET ?"
        cursor.execute(data_query, params + [limit, offset])
        results = [dict(row) for row in cursor.fetchall()]

        return {"total": total_records, "records": results, "columns": columns}

    def get_abilities_by_pokemon_id(self, pokemon_id: int) -> list[dict]:
        """指定されたポケモンIDが持つ特性を、pokemonsテーブルのabilitiesカラム(カンマ区切りのID)から取得する。"""
        cursor = self.get_cursor()
        
        # 1. pokemonsテーブルからabilitiesカラム（カンマ区切りID文字列）を取得
        cursor.execute("SELECT abilities FROM pokemons WHERE id = ?", (pokemon_id,))
        row = cursor.fetchone()
        if not row or not row['abilities']:
            return []

        try:
            # 2. カンマで分割し、数値のIDリストに変換
            ability_ids = [int(id_str) for id_str in row['abilities'].split(',') if id_str.strip().isdigit()]
            if not ability_ids:
                return []
        except (ValueError, AttributeError):
            return []

        # 3. 特性IDリストを使ってabilitiesテーブルから詳細を一括取得
        placeholders = ', '.join('?' for _ in ability_ids)
        query = f"SELECT id, name, name_ja FROM abilities WHERE id IN ({placeholders})"
        
        cursor.execute(query, ability_ids)
        return [dict(row) for row in cursor.fetchall()]



    def get_moves_by_pokemon_id(self, pokemon_id: int) -> list[dict]:
        """指定されたポケモンIDが覚える技を、pokemonsテーブルのmovesカラム(カンマ区切りのID)から取得する。"""
        cursor = self.get_cursor()
        
        # 1. pokemonsテーブルからmovesカラム（カンマ区切りID文字列）を取得
        cursor.execute("SELECT moves FROM pokemons WHERE id = ?", (pokemon_id,))
        row = cursor.fetchone()
        if not row or not row['moves']:
            return []

        try:
            # 2. カンマで分割し、数値のIDリストに変換
            move_ids = [int(id_str) for id_str in row['moves'].split(',') if id_str.strip().isdigit()]
            if not move_ids:
                return []
        except (ValueError, AttributeError):
            return []

        # 3. 技IDリストを使ってmovesテーブルから詳細を一括取得
        placeholders = ', '.join('?' for _ in move_ids)
        query = f"SELECT id, name, name_ja FROM moves WHERE id IN ({placeholders})"
        
        cursor.execute(query, move_ids)
        return [dict(row) for row in cursor.fetchall()]

    def get_moves_by_type(self, move_type: str, category: str, limit: int = 10) -> list[dict]:
        """指定されたタイプとカテゴリの技を取得する（威力順）。"""
        cursor = self.get_cursor()
        query = """
            SELECT *
            FROM moves
            WHERE type = ? AND category = ? AND power > 0
            ORDER BY power DESC
            LIMIT ?
        """
        return [dict(row) for row in cursor.fetchall()]

    # --- Dashboard ---

