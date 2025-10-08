import sqlite3
import os

def add_table():
    """
    既存のデータベースに raw_battle_events テーブルを追加する。
    テーブルが既に存在する場合は何もしない。
    """
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'pokemon_ai.db')
        print(f"データベースファイル: {db_path}")

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS raw_battle_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id INTEGER NOT NULL,
            sequence INTEGER NOT NULL,
            log_timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
            roi_name TEXT NOT NULL,
            ocr_text TEXT,
            FOREIGN KEY (battle_id) REFERENCES battles (battle_id),
            UNIQUE(battle_id, sequence, roi_name)
        );
        """

        print("データベースに接続しています...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("接続しました。")

        print("raw_battle_events テーブルを作成（または存在を確認）します...")
        cursor.execute(create_table_sql)

        conn.commit()
        conn.close()

        print("\nデータベースの更新が正常に完了しました。")

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")

if __name__ == '__main__':
    add_table()
