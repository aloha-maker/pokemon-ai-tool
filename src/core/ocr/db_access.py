import sqlite3
import os
import json
import time

class DatabaseManager:
    """
    データベースへの接続と操作を管理するクラス。
    アプリケーションの他モジュールは、このクラスを通じてデータベースにアクセスする。
    """
    def __init__(self, db_path=None):
        """
        DatabaseManagerを初期化する。
        db_pathが指定されない場合、プロジェクトルートからの相対パスを使用する。
        """
        from flask import current_app

        if db_path is None:
            db_url = current_app.config.get('DATABASE_URL')
            if db_url and db_url.startswith('sqlite:///'):
                self.db_path = db_url.replace('sqlite:///', '')
            else:
                self.db_path = r'C:\pokemon-ai-tool\data\pokemon_ai.db'
        else:
            self.db_path = db_path
        self.conn = None

    def __enter__(self):
        """コンテキストマネージャの開始時にデータベースに接続する。"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャの終了時にデータベース接続を閉じる。"""
        self.close()

    def connect(self):
        """データベースに接続する。"""
        if self.conn is None:
            try:
                print(f"Trying to open DB at: {self.db_path}")
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                print(f"Error connecting to database: {e}")
                raise

    def close(self):
        """データベース接続を閉じる。"""
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

    def get_pokemon_names_by_battle_id(self, battle_id: str) -> dict | None:
        """
        指定した battle_id に紐づくポケモン名を取得する。
        自分のポケモン・相手のポケモンをそれぞれリストで返す。
        """
        cursor = self.get_cursor()
        query = """
            SELECT 
                p.pokemon_name,
                p.is_opponent
            FROM parties_log p
            WHERE p.battle_id = ?
            ORDER BY p.is_opponent, p.pokemon_id
        """
        cursor.execute(query, (battle_id,))
        rows = cursor.fetchall()

        if not rows:
            return None

        my_pokemons = [row["pokemon_name"] for row in rows if not row["is_opponent"]]
        opponent_pokemons = [row["pokemon_name"] for row in rows if row["is_opponent"]]

        return {
            "battle_id": battle_id,
            "my_pokemons": my_pokemons,
            "opponent_pokemons": opponent_pokemons
        }


if __name__ == "__main__":
    with DatabaseManager() as db:
        battle_id = "BATTLE-20251013-0001"
        result = db.get_pokemon_names_by_battle_id(battle_id)
        if result:
            print(f"バトルID: {result['battle_id']}")
            print("自分のポケモン:", ", ".join(result["my_pokemons"]))
            print("相手のポケモン:", ", ".join(result["opponent_pokemons"]))
        else:
            print("該当するバトルが見つかりませんでした。")
