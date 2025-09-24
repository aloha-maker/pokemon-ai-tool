import csv
import sqlite3
import os

# --- 設定項目 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MASTER_DATA_DIR = os.path.join(DATA_DIR, "master_data")
DB_PATH = os.path.join(DATA_DIR, "pokemon_ai.db")
SCHEMA_PATH = os.path.join(DATA_DIR, "schema.sql")

# CSVファイルのパス
POKEMONS_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemons.csv")
MOVES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "moves.csv")
TYPES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "types.csv")
ABILITIES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "abilities.csv")
NATURES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "natures.csv")
ITEMS_CSV_PATH = os.path.join(MASTER_DATA_DIR, "items.csv")

# --- データベース初期化 ---
def initialize_database():
    """データベースファイルを初期化し、スキーマに基づいてテーブルを作成する"""
    print("--- データベースの初期化開始 ---")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"既存のデータベース '{DB_PATH}' を削除しました。")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"データベース '{DB_PATH}' を作成し、接続しました。")
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        conn.commit()
        print("テーブルの作成が完了しました。")
        return conn
    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
        return None
    finally:
        print("--- データベースの初期化完了 ---")


# --- データ投入 ---
def seed_data(conn):
    """CSVファイルからデータを読み込み、データベースに投入する"""
    print("--- データベースへのデータ投入開始 ---")
    if not conn: return
    cursor = conn.cursor()
    try:
        def seed_from_csv(path, table, columns):
            print(f"'{path}' から {table} データを投入中...")
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーをスキップ
                placeholders = ', '.join('?' * len(columns))
                cursor.executemany(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", reader)
            print(f"{table} データの投入が完了しました。")

        seed_from_csv(POKEMONS_CSV_PATH, "pokemons", ["id", "name", "name_ja", "type1", "type2", "hp", "attack", "defense", "sp_attack", "sp_defense", "speed"])
        seed_from_csv(TYPES_CSV_PATH, "types", ["id", "name", "name_ja"])
        seed_from_csv(ABILITIES_CSV_PATH, "abilities", ["id", "name", "name_ja"])
        seed_from_csv(NATURES_CSV_PATH, "natures", ["id", "name", "name_ja", "increased_stat", "decreased_stat"])
        seed_from_csv(ITEMS_CSV_PATH, "items", ["id", "name", "name_ja"])

        seed_from_csv(MOVES_CSV_PATH, "moves", ["id", "name", "name_ja", "type", "category", "power", "accuracy"])

        conn.commit()
        print("データベースへのコミットが完了しました。")
    except Exception as e:
        print(f"データ投入中にエラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("データベース接続を閉じました。")
        print("--- データベースへのデータ投入完了 ---")


# --- メイン処理 ---
def main():
    """データベースの再初期化とデータ投入を実行する"""
    conn = initialize_database()
    if conn:
        seed_data(conn)
    print("データベースの再シードがすべて完了しました。")

if __name__ == '__main__':
    main()
