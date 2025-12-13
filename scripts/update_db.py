import sqlite3
import os
import argparse
import re

def recreate_tables(tables_to_recreate):
    """
    指定されたテーブルを schema.sql に基づいて再構築する。
    注意: 指定されたテーブルのデータはすべて消去されます。
    """
    conn = None
    try:
        # --- Path setup ---
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'data', 'pokemon_ai.db')
        schema_path = os.path.join(base_dir, 'data', 'schema.sql')
        
        print(f"データベースファイル: {db_path}")
        print(f"スキーマファイル: {schema_path}")
        print(f"再構築対象のテーブル: {', '.join(tables_to_recreate)}")

        # --- Read Schema ---
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # --- Recreate tables ---
        print("データベースに接続しています...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("接続しました。")

        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Drop tables first (in user-provided order, reversed)
        print("既存テーブルを削除します...")
        for table_name in reversed(tables_to_recreate):
            print(f"  - 削除中: {table_name}")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")

        # Find and execute CREATE statements from schema.sql
        print("新しいスキーマでテーブルを作成します...")
        sql_statements = [s.strip() for s in sql_script.split(';')]
        
        for table_name in tables_to_recreate:
            found_statement = None
            for statement in sql_statements:
                if re.search(f"CREATE TABLE( IF NOT EXISTS)?\\s+`?{table_name}`?\\s*\\(", statement, re.IGNORECASE):
                    found_statement = statement
                    break
            
            if found_statement:
                print(f"  - 作成中: {table_name}...")
                cursor.execute(found_statement + ';')
            else:
                print(f"  - 警告: テーブル '{table_name}' のCREATE文がschema.sqlに見つかりませんでした。")

        cursor.execute("PRAGMA foreign_keys = ON;")
        
        conn.commit()
        print("\nデータベースの更新が正常に完了しました。")

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="schema.sqlから特定のテーブルを再構築します。テーブルのデータはすべて失われます。",
        epilog="例: python update_db.py battles parties_log raw_battle_events"
    )
    parser.add_argument(
        'tables', 
        nargs='+', 
        help='再構築するテーブル名のリスト。依存関係のあるテーブルは、依存される側を先に指定してください (例: battles parties_log)。'
    )
    
    args = parser.parse_args()
    recreate_tables(args.tables)
