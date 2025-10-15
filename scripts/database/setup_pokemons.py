import sqlite3
import pandas as pd
import os
import sys

# 親ディレクトリをsys.pathに追加して、commonをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from common import DB_PATH, POKEMONS_CSV_PATH, MASTER_DATA_DIR, SCHEMA_DIR

SPECIAL_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemon_special_ja.csv")
POKEMON_ABILITIES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemon_abilities.csv")
POKEMON_MOVES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemon_moves.csv")

def setup_pokemons():
    """
    pokemonsテーブルを再作成し、データを投入する (DROP, CREATE, INSERT)
    """
    table_name = "pokemons"
    schema_path = os.path.join(SCHEMA_DIR, f"{table_name}.sql")
    print(f"--- '{table_name}' テーブルのセットアップ開始 ---")

    # --- ファイル存在チェック ---
    required_files = [POKEMONS_CSV_PATH, SPECIAL_CSV_PATH, DB_PATH, schema_path]
    for path in required_files:
        if not os.path.exists(path):
            print(f"エラー: 必要なファイルが見つかりません: {path}")
            return

    conn = None
    try:
        # --- 1. データ準備 ---
        print("CSVファイルを読み込んでデータを準備しています...")
        
        # 特殊フォームデータの読み込み
        special_df = pd.read_csv(SPECIAL_CSV_PATH)
        special_map = special_df.set_index('id').to_dict('index')
        
        # ポケモンデータの読み込み
        pokemons_df = pd.read_csv(POKEMONS_CSV_PATH)

        # 特殊フォームデータの適用
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
        
        # --- 2. abilitiesとmovesのデータを関連CSVから設定 ---
        print("abilitiesとmovesのデータを関連CSVから設定しています...")
        
        # 初期化（空の文字列で設定）
        pokemons_df['moves'] = ''
        pokemons_df['abilities'] = ''
        
        # pokemon_abilities.csv が存在する場合、abilitiesを設定
        if os.path.exists(POKEMON_ABILITIES_CSV_PATH):
            pokemon_abilities_df = pd.read_csv(POKEMON_ABILITIES_CSV_PATH)
            
            # ポケモンIDごとに能力を設定（ability_idsをそのまま使用）
            for _, row in pokemon_abilities_df.iterrows():
                pokemon_id = row['pokemon_id']
                ability_ids = row['ability_ids']
                if pokemon_id in pokemons_df['id'].values:
                    pokemons_df.loc[pokemons_df['id'] == pokemon_id, 'abilities'] = str(ability_ids)
            print(f"  - {len(pokemon_abilities_df)} ポケモンのabilitiesを設定")
        else:
            print(f"  - 警告: {POKEMON_ABILITIES_CSV_PATH} が見つからないため、abilitiesは空で設定されます")
        
        # pokemon_moves.csv が存在する場合、movesを設定
        if os.path.exists(POKEMON_MOVES_CSV_PATH):
            pokemon_moves_df = pd.read_csv(POKEMON_MOVES_CSV_PATH)
            
            # ポケモンIDごとに技を設定（move_idsをそのまま使用）
            for _, row in pokemon_moves_df.iterrows():
                pokemon_id = row['pokemon_id']
                move_ids = row['move_ids']
                if pokemon_id in pokemons_df['id'].values:
                    pokemons_df.loc[pokemons_df['id'] == pokemon_id, 'moves'] = str(move_ids)
            print(f"  - {len(pokemon_moves_df)} ポケモンのmovesを設定")
        else:
            print(f"  - 警告: {POKEMON_MOVES_CSV_PATH} が見つからないため、movesは空で設定されます")

        # --- 3. データベース投入用のデータ準備 ---
        db_columns = [
            "id", "name", "name_ja", "base_id", "type1", "type2", "hp", 
            "attack", "defense", "sp_attack", "sp_defense", "speed", 
            "moves", "abilities"
        ]
        final_df = pokemons_df[db_columns]
        data_to_insert = [tuple(row) for row in final_df.itertuples(index=False)]

        # --- 4. CREATE文の準備 ---
        print(f"スキーマファイル '{schema_path}' を読み込んでいます...")
        with open(schema_path, 'r', encoding='utf-8') as f:
            create_sql = f.read()

        # --- 5. データベース処理 ---
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

        # --- 6. 設定状況のサマリー表示 ---
        abilities_set = final_df[final_df['abilities'] != ''].shape[0]
        moves_set = final_df[final_df['moves'] != ''].shape[0]
        print(f"設定状況: {abilities_set}/{len(final_df)} ポケモンにabilities設定, {moves_set}/{len(final_df)} ポケモンにmoves設定")

    except Exception as e:
        print(f"\n処理中にエラーが発生しました: {e}")
        if conn: conn.rollback()
    finally:
        if conn:
            conn.close()
        print(f"--- '{table_name}' テーブルのセットアップ完了 ---")

if __name__ == '__main__':
    setup_pokemons()