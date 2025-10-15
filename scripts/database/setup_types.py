import sqlite3
import pandas as pd
import os
import sys

# 親ディレクトリをsys.pathに追加して、commonをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from common import DB_PATH, TYPES_CSV_PATH, SCHEMA_DIR

def setup_types():
    """
    typesテーブルを再作成し、データを投入する (DROP, CREATE, INSERT)
    """
    table_name = "types"
    schema_path = os.path.join(SCHEMA_DIR, f"{table_name}.sql")
    print(f"--- '{table_name}' テーブルのセットアップ開始 ---")

    # --- ファイル存在チェック ---
    for path in [TYPES_CSV_PATH, DB_PATH, schema_path]:
        if not os.path.exists(path):
            print(f"エラー: 必要なファイルが見つかりません: {path}")
            return

    conn = None
    try:
        # --- 1. データ準備 ---
        print("CSVファイルを読み込んでデータを準備しています...")
        types_df = pd.read_csv(TYPES_CSV_PATH)
        
        db_columns = ["id", "name", "name_ja"]
        data_to_insert = [tuple(row) for row in types_df[db_columns].itertuples(index=False)]

        # --- 2. CREATE文の準備 ---
        print(f"スキーマファイル '{schema_path}' を読み込んでいます...")
        with open(schema_path, 'r', encoding='utf-8') as f:
            create_sql = f.read()

        # --- 3. データベース処理 ---
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print(f"'{table_name}' テーブルを再作成しています...")
        cursor.execute("PRAGMA foreign_keys=OFF;")
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        cursor.execute(create_sql)
        cursor.execute("PRAGMA foreign_keys=ON;")
        print("テーブルの再作成が完了しました。")

        print(f"'{table_name}' テーブルにデータを投入しています...")
        placeholders = ', '.join('?' * len(db_columns))
        insert_sql = f"INSERT INTO {table_name} ({ ', '.join(db_columns)}) VALUES ({placeholders})"
        cursor.executemany(insert_sql, data_to_insert)
        
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
    setup_types()