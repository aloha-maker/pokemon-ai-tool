import sqlite3
import os

def apply_schema_updates():
    """
    schemaディレクトリ内のすべての.sqlファイルを読み込み、
    データベースに適用してテーブルとインデックスを作成します。
    「IF NOT EXISTS」を使用しているため、何度実行しても安全です。
    """
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'pokemon_ai.db')
    schema_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'schema')

    print(f"データベース '{db_path}' にスキーマ更新を適用します...")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            sql_files = sorted([f for f in os.listdir(schema_dir) if f.endswith('.sql')])

            for sql_file in sql_files:
                file_path = os.path.join(schema_dir, sql_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                    try:
                        cursor.executescript(sql_script)
                        print(f"  - {sql_file} を正常に適用しました。")
                    except sqlite3.Error as e:
                        print(f"  - エラー: {sql_file} の適用中にエラーが発生しました: {e}")
                        conn.rollback()
                        return

            print("すべてのスキーマ更新が正常に適用されました。")
    except sqlite3.Error as e:
        print(f"データベース接続中にエラーが発生しました: {e}")

if __name__ == '__main__':
    apply_schema_updates()
