import sqlite3
import os
import json

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
        if db_path is None:
            # プロジェクトのルートディレクトリを基準にDBファイルのパスを構築
            self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'pokemon_ai.db')
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

    def get_battle_history(self, limit: int = 50) -> list[dict]:
        """対戦履歴の一覧を取得する。"""
        cursor = self.get_cursor()
        cursor.execute("SELECT * FROM battle_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_battle_stats(self) -> dict:
        """勝率などの統計データを計算して取得する。"""
        cursor = self.get_cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM battle_logs")
        total_matches = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as wins FROM battle_logs WHERE result = 'win'")
        total_wins = cursor.fetchone()['wins']

        win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

        return {
            "total_matches": total_matches,
            "total_wins": total_wins,
            "win_rate": round(win_rate, 1)
        }

    def add_battle_log(self, log_data: dict) -> int:
        """
        対戦履歴を `battle_logs` テーブルに追加する。
        log_dataには result, opponent_party, my_party, my_selection が含まれることを想定。
        戻り値は追加されたレコードのID。
        """
        cursor = self.get_cursor()

        # my_partyとmy_selectionをbattle_dataにJSONとして格納
        battle_data = {
            "my_party": log_data.get('my_party'),
            "my_selection": log_data.get('my_selection')
        }

        # my_party_idは暫定的に1とする。将来的にはpartiesテーブルへの登録とID取得が必要。
        my_party_id = 1 

        cursor.execute(
            "INSERT INTO battle_logs (result, opponent_party, my_party_id, battle_data) VALUES (?, ?, ?, ?)",
            (
                log_data['result'],
                json.dumps(log_data.get('opponent_party')),
                my_party_id,
                json.dumps(battle_data)
            )
        )
        self.conn.commit()
        return cursor.lastrowid

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
