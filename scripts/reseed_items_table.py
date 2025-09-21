
import sqlite3
import os
import csv

# setup_database.pyから関連する関数とパスをインポート
from setup_database import generate_csv_files, ITEMS_CSV_PATH

# --- 設定項目 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "pokemon_ai.db")

def main():
    """ `items` テーブルを再構築する """
    print("--- `items` テーブルの再構築を開始します ---")

    # 1. 最新のCSVファイルを生成 (重複排除されたitems.csvが作られる)
    print("ステップ1: マスターデータCSVファイルを再生成します...")
    try:
        generate_csv_files()
        print("-> CSVファイルの生成が完了しました。")
    except Exception as e:
        print(f"CSVファイルの生成中にエラーが発生しました: {e}")
        return

    # 2. データベースに接続し、itemsテーブルをクリアしてデータを再投入
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"\nステップ2: データベース '{DB_PATH}' に接続しました。")

        # テーブルをクリア
        print("-> `items` テーブルの既存データを削除します...")
        cursor.execute("DELETE FROM items")
        print("-> 削除が完了しました。")

        # CSVからデータを投入
        print(f"-> '{ITEMS_CSV_PATH}' からデータを投入します...")
        with open(ITEMS_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # ヘッダーをスキップ
            columns = ["id", "name", "name_ja"]
            placeholders = ', '.join('?' * len(columns))
            cursor.executemany(f"INSERT INTO items ({', '.join(columns)}) VALUES ({placeholders})", reader)
        
        conn.commit()
        print("-> データの投入が完了しました。")
        print("\n--- `items` テーブルの再構築が正常に完了しました ---")

    except Exception as e:
        print(f"データベース処理中にエラーが発生しました: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("データベース接続を閉じました。")

if __name__ == '__main__':
    main()
