import sqlite3
import pandas as pd
import os
import sys

# 親ディレクトリをsys.pathに追加して、commonをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from common import DB_PATH, POKEMONS_CSV_PATH, MASTER_DATA_DIR

# pokemon_special_ja.csv のパスを定義
SPECIAL_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemon_special_ja.csv")

def seed_pokemons():
    """
    pokemons.csvとpokemon_special_ja.csvを統合し、pokemonsテーブルに再投入する。
    base_idを決定し、name_jaをフォルム名で更新後、DELETE & INSERT を行う。
    """
    table_name = "pokemons"
    print(f"--- B案: '{table_name}' テーブルへのデータ再投入開始 (統合処理) ---")

    # --- ファイル存在チェック ---
    if not os.path.exists(POKEMONS_CSV_PATH):
        print(f"エラー: CSVファイル '{POKEMONS_CSV_PATH}' が見つかりません。")
        return
    if not os.path.exists(SPECIAL_CSV_PATH):
        print(f"エラー: CSVファイル '{SPECIAL_CSV_PATH}' が見つかりません。")
        return
    if not os.path.exists(DB_PATH):
        print(f"エラー: データベース '{DB_PATH}' が見つかりません。先に `initialize_database.py` を実行してください。")
        return

    conn = None
    try:
        # --- 1. データ準備 ---
        print("CSVファイルを読み込んでいます...")
        special_df = pd.read_csv(SPECIAL_CSV_PATH)
        # id をキーに、'base_id' と 'name_ja_form' を含む辞書を作成
        special_map = special_df.set_index('id').to_dict('index')

        pokemons_df = pd.read_csv(POKEMONS_CSV_PATH)

        # --- 2. base_id と name_ja の更新 ---
        def apply_special_data(row):
            special_data = special_map.get(row['id'])
            if special_data:
                # フォルム情報があれば、base_id と name_ja を更新
                row['base_id'] = special_data['base_id']
                row['name_ja'] = special_data['name_ja_form']
            else:
                # なければ、自身のidをbase_idに設定
                row['base_id'] = row['id']
            return row

        print("フォルム情報を統合しています...")
        pokemons_df = pokemons_df.apply(apply_special_data, axis=1)
        
        # base_id を整数型に変換
        pokemons_df['base_id'] = pokemons_df['base_id'].astype(int)

        # --- 3. データベース投入用データ整形 ---
        db_columns = [
            "id", "name", "name_ja", "base_id", "type1", "type2", "hp", 
            "attack", "defense", "sp_attack", "sp_defense", "speed", 
            "moves", "abilities"
        ]
        pokemons_df['moves'] = ''
        pokemons_df['abilities'] = ''
        final_df = pokemons_df[db_columns]

        # --- 4. データベース処理 ---
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print(f"既存の '{table_name}' データを削除しています...")
        cursor.execute(f"DELETE FROM {table_name};")

        print(f"'{table_name}' テーブルにデータを投入しています...")
        data_to_insert = [tuple(row) for row in final_df.itertuples(index=False)]
        
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
        print(f"--- '{table_name}' テーブルへのデータ再投入完了 ---")

if __name__ == '__main__':
    seed_pokemons()
