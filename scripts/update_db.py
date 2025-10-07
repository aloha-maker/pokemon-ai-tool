import sqlite3
import os

def update_database():
    """
    既存のデータベースに新しいテーブルを追加する。
    """
    try:
        # データベースファイルのパスを構築
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pokemon_ai.db')
        print(f"データベースファイル: {db_path}")

        # 追加するテーブルのCREATE文
        create_battles_table = """
        CREATE TABLE IF NOT EXISTS battles (
            battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_date TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
            season INTEGER,
            regulation TEXT,
            battle_format TEXT NOT NULL CHECK(battle_format IN ('シングル', 'ダブル')),
            my_rank INTEGER,
            opponent_rank INTEGER,
            result TEXT NOT NULL CHECK(result IN ('win', 'lose', 'unknown')),
            my_first_pokemon TEXT,
            opponent_first_pokemon TEXT,
            memo TEXT
        );
        """

        create_pokemons_log_table = """
        CREATE TABLE IF NOT EXISTS pokemons_log (
            pokemon_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pokemon_name TEXT NOT NULL,
            nickname TEXT,
            moves TEXT,
            terastal_type TEXT,
            item TEXT,
            ability TEXT,
            UNIQUE(pokemon_name, nickname, moves, terastal_type, item, ability)
        );
        """

        create_parties_log_table = """
        CREATE TABLE IF NOT EXISTS parties_log (
            party_id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id INTEGER NOT NULL,
            pokemon_id INTEGER,
            pokemon_name TEXT NOT NULL,
            is_opponent BOOLEAN NOT NULL,
            is_selected BOOLEAN NOT NULL,
            FOREIGN KEY (battle_id) REFERENCES battles (battle_id),
            FOREIGN KEY (pokemon_id) REFERENCES pokemons_log (pokemon_id)
        );
        """

        # データベースに接続
        print("データベースに接続しています...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("接続しました。")

        # テーブルを作成
        print("battles テーブルを作成します...")
        cursor.execute(create_battles_table)
        print("pokemons_log テーブルを作成します...")
        cursor.execute(create_pokemons_log_table)
        print("parties_log テーブルを作成します...")
        cursor.execute(create_parties_log_table)

        # 接続を閉じる
        conn.commit()
        conn.close()

        print("\nデータベースの更新が正常に完了しました。")
        print("新しいテーブル (battles, pokemons_log, parties_log) が追加されました。")

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")

if __name__ == '__main__':
    update_database()
