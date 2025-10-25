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
        self.conn = conn
        self._external_conn = conn is not None

        if not self._external_conn:
            if db_path is None:
                try:
                    from flask import current_app
                    db_url = current_app.config.get('DATABASE_URL')
                    if db_url and db_url.startswith('sqlite:///'):
                        self.db_path = db_url.replace('sqlite:///', '')
                    else:
                        raise RuntimeError("No database URL configured and no fallback path available.")
                except RuntimeError:
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



    # --- Dashboard ---

