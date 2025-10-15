import sqlite3
import csv
import os
import sys
import re

# 親ディレクトリをsys.pathに追加して、commonをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from common import DB_PATH, MOVES_CSV_PATH, SCHEMA_PATH

def get_create_table_sql(schema_content, table_name):
    """スキーマSQLから指定されたテーブルのCREATE文を抽出する"""
    pattern = re.compile(f"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?{table_name}\s*\(.*\);", re.DOTALL | re.IGNORECASE)
    match = pattern.search(schema_content)
    if match:
        return match.group(0)
    return None

def setup_moves():
    """
    movesテーブルを再作成し、データを投入する (DROP, CREATE, INSERT)
    """
    table_name = "moves"
    csv_path = MOVES_CSV_PATH
    db_columns = ["id", "name", "name_ja", "type", "category", "power", "accuracy", "pp"]
    print(f"--- A案: '{table_name}' テーブルのセットアップ開始 ---")

    # --- ファイル存在チェック ---
    for path in [csv_path, DB_PATH, SCHEMA_PATH]:
        if not os.path.exists(path):
            print(f"エラー: 必要なファイルが見つかりません: {path}")
            return

    conn = None
    try:
        # --- 1. CREATE文の準備 ---
        print("スキーマからCREATE文を読み込んでいます...")
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        create_sql = get_create_table_sql(schema_sql, table_name)
        if not create_sql:
            raise Exception(f"'{SCHEMA_PATH}' から '{table_name}' のCREATE文が見つかりませんでした。")

        # --- 2. データベース処理 ---
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print(f"'{table_name}' テーブルを再作成しています...")
        cursor.execute("PRAGMA foreign_keys=OFF;")
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        cursor.execute(create_sql)
        cursor.execute("PRAGMA foreign_keys=ON;")
        print("テーブルの再作成が完了しました。")

        # --- 3. データ投入 ---
        print(f"'{table_name}' テーブルにデータを投入しています...")
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ
            
            placeholders = ', '.join('?' * len(db_columns))
            insert_sql = f"INSERT INTO {table_name} ({ ', '.join(db_columns)}) VALUES ({placeholders})"
            
            cursor.executemany(insert_sql, reader)

        conn.commit()
        print(f"{cursor.rowcount} 件のデータが '{table_name}' テーブルに投入されました。")

    except Exception as e:
        print(f"\n処理中にエラーが発生しました: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            conn.close()
        print(f"--- '{table_name}' テーブルのセットアップ完了 ---")

if __name__ == '__main__':
    setup_moves()
