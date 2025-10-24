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

