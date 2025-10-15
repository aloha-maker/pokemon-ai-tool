import sqlite3
import pandas as pd
import os
import sys
import re

# 親ディレクトリをsys.pathに追加して、commonをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from common import DB_PATH, POKEMONS_CSV_PATH, MASTER_DATA_DIR, SCHEMA_PATH

SPECIAL_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemon_special_ja.csv")

def get_create_table_sql(schema_content, table_name):
    """スキーマSQLから指定されたテーブルのCREATE文を抽出する"""
    # CREATE TABLE table_name (...) ; という形式のSQL文を抽出する正規表現
    pattern = re.compile(f"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?{table_name}\s*\(.*\);", re.DOTALL | re.IGNORECASE)
    match = pattern.search(schema_content)
    if match:
        return match.group(0)
    return None

def setup_pokemons():
    """
    pokemonsテーブルを再作成し、データを投入する (DROP, CREATE, INSERT)
    """
    table_name = "pokemons"
    print(f"--- A案: '{table_name}' テーブルのセットアップ開始 ---")

    # --- ファイル存在チェック ---
    for path in [POKEMONS_CSV_PATH, SPECIAL_CSV_PATH, DB_PATH, SCHEMA_PATH]:
        if not os.path.exists(path):
            print(f"エラー: 必要なファイルが見つかりません: {path}")
            return

    conn = None
    try:
        # --- 1. データ準備 (seed_pokemons.pyと同じ) ---
        print("CSVファイルを読み込んでデータを準備しています...")
        special_df = pd.read_csv(SPECIAL_CSV_PATH)
        special_map = special_df.set_index('id').to_dict('index')
        pokemons_df = pd.read_csv(POKEMONS_CSV_PATH)

        def apply_special_data(row):
            special_data = special_map.get(row['id'])
            if special_data:
                row['base_id'] = special_data['base_id']
                row['name_ja'] = special_data['name_ja_form']
            else:
                row['base_id'] = row['id']
            return row

        pokemons_df = pokemons_df.apply(apply_special_data, axis=1)
        pokemons_df['base_id'] = pokemons_df['base_id'].astype(int)
        pokemons_df['moves'] = ''
        pokemons_df['abilities'] = ''

        db_columns = [
            "id", "name", "name_ja", "base_id", "type1", "type2", "hp", 
            "attack", "defense", "sp_attack", "sp_defense", "speed", 
            "moves", "abilities"
        ]
        final_df = pokemons_df[db_columns]
        data_to_insert = [tuple(row) for row in final_df.itertuples(index=False)]

        # --- 2. CREATE文の準備 ---
        print("スキーマからCREATE文を読み込んでいます...")
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        create_sql = get_create_table_sql(schema_sql, table_name)
        if not create_sql:
            raise Exception(f"'{SCHEMA_PATH}' から '{table_name}' のCREATE文が見つかりませんでした。")

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
    setup_pokemons()
