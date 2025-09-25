
import sqlite3
import os

# このスクリプトは、pokemon_abilities テーブルを作成し、
# ポケモンと特性の正しい関連性を設定します。

def get_db_path():
    """データベースファイルの絶対パスを取得する"""
    return os.path.join(os.path.dirname(__file__), '..', 'data', 'pokemon_ai.db')

def execute_queries(conn, queries):
    """複数のSQLクエリを実行する"""
    cursor = conn.cursor()
    for query in queries:
        try:
            cursor.execute(query)
            print(f"Successfully executed: {query}")
        except sqlite3.Error as e:
            print(f"Error executing query '{query}': {e}")
    conn.commit()

def get_id_from_name(cursor, table, name_column, name):
    """名前からIDを取得する"""
    try:
        cursor.execute(f"SELECT id FROM {table} WHERE {name_column} = ?", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            print(f"Warning: Could not find ID for {name} in {table}.")
            return None
    except sqlite3.Error as e:
        print(f"Error fetching ID for {name}: {e}")
        return None

def main():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. pokemon_abilities テーブルを作成
    create_table_query = """
    CREATE TABLE IF NOT EXISTS pokemon_abilities (
        pokemon_id INTEGER NOT NULL,
        ability_id INTEGER NOT NULL,
        is_hidden BOOLEAN DEFAULT 0,
        PRIMARY KEY (pokemon_id, ability_id),
        FOREIGN KEY (pokemon_id) REFERENCES pokemons(id),
        FOREIGN KEY (ability_id) REFERENCES abilities(id)
    );
    """
    execute_queries(conn, [create_table_query])
    print("--- `pokemon_abilities` table created or already exists. ---")

    # 2. ポケモンと特性の関連データを定義
    # (ポケモン名, [通常特性1, 通常特性2, ...], [隠れ特性])
    pokemon_ability_map = {
        "フシギダネ": (["しんりょく"], ["ようりょくそ"]),
        "リザードン": (["もうか"], ["サンパワー"]),
        "カビゴン": (["めんえき", "あついしぼう"], ["くいしんぼう"]),
        "カイリュー": (["せいしんりょく"], ["マルチスケイル"]),
        "ハッサム": (["むしのしらせ", "テクニシャン"], ["ライトメタル"]),
        "ドラパルト": (["クリアボディ", "すりぬけ"], ["のろわれボディ"]),
        "サーフゴー": (["おうごんのからだ"], []),
        "キョジオーン": (["きよめのしお", "がんじょう"], ["クリアボディ"]),
        "ヘイラッシャ": (["てんねん", "どんかん"], ["みずのベール"]),
        "マスカーニャ": (["しんりょく"], ["へんげんじざい"]),
        "ラウドボーン": (["もうか"], ["てんねん"]),
        "ウェーニバル": (["げきりゅう"], ["じしんかじょう"]),
        "ドドゲザン": (["まけんき", "そうだいしょう"], ["プレッシャー"]),
        "キノガッサ": (["ほうし", "ポイズンヒール"], ["テクニシャン"]),
        "ミミッキュ": (["ばけのかわ"], []),
    }

    # 3. データをテーブルに挿入
    print("--- Inserting pokemon-ability relationships... ---")
    for p_name, (normal_abilities, hidden_abilities) in pokemon_ability_map.items():
        pokemon_id = get_id_from_name(cursor, 'pokemons', 'name_ja', p_name)
        if not pokemon_id:
            continue

        # 通常特性
        for a_name in normal_abilities:
            ability_id = get_id_from_name(cursor, 'abilities', 'name_ja', a_name)
            if ability_id:
                try:
                    cursor.execute("INSERT OR IGNORE INTO pokemon_abilities (pokemon_id, ability_id, is_hidden) VALUES (?, ?, 0)", (pokemon_id, ability_id))
                except sqlite3.Error as e:
                    print(f"Error inserting {p_name}-{a_name}: {e}")
        
        # 隠れ特性
        for a_name in hidden_abilities:
            ability_id = get_id_from_name(cursor, 'abilities', 'name_ja', a_name)
            if ability_id:
                try:
                    cursor.execute("INSERT OR IGNORE INTO pokemon_abilities (pokemon_id, ability_id, is_hidden) VALUES (?, ?, 1)", (pokemon_id, ability_id))
                except sqlite3.Error as e:
                    print(f"Error inserting hidden {p_name}-{a_name}: {e}")

    conn.commit()
    print("--- Finished inserting relationships. ---")
    
    conn.close()
    print("Database connection closed.")

if __name__ == "__main__":
    main()
