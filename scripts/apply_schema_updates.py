
import sqlite3
import os
import re
import csv

# setup_database.pyからCSV生成関数をインポート
# NOTE: このスクリプトはsetup_database.pyに依存しているため、同じディレクトリ構造を前提とします
from setup_database import generate_csv_files, \
    TYPES_CSV_PATH, ABILITIES_CSV_PATH, NATURES_CSV_PATH, ITEMS_CSV_PATH

# --- 設定項目 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "pokemon_ai.db")
SCHEMA_PATH = os.path.join(DATA_DIR, "schema.sql")

def apply_schema_changes(conn):
    """ `schema.sql` を解析し、DROP TABLE以外を実行する """
    print("--- スキーマの変更を適用します (デバッグモード) ---")
    cursor = conn.cursor()
    
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        print("[DEBUG] schema.sql の内容を読み込みました。")

        # DROP TABLE文を正規表現で除去
        cleaned_script = re.sub(r"DROP TABLE IF EXISTS .*?;", "", sql_script, flags=re.IGNORECASE | re.DOTALL)
        if "DROP TABLE" in cleaned_script.upper():
            print("[DEBUG] 警告: DROP TABLE文の除去が不完全かもしれません。")
        else:
            print("[DEBUG] DROP TABLE文を正常に除去しました。")

        # スクリプトをセミコロンで分割して、個別のSQL文にする
        statements = [s.strip() for s in cleaned_script.split(';') if s.strip()]
        print(f"[DEBUG] {len(statements)}個のSQL文を検出しました。")

        # 各SQL文を個別に実行
        for i, stmt in enumerate(statements):
            print(f"\n[DEBUG] 実行中のSQL文 ({i+1}/{len(statements)}):")
            print(f">>> {stmt[:100]}..." if len(stmt) > 100 else f">>> {stmt}")
            try:
                cursor.execute(stmt)
                print("-> 成功")
            except sqlite3.OperationalError as e:
                print(f"-> エラー: {e}")
        
        conn.commit()
        print("\nスキーマの適用が完了しました。")

    except Exception as e:
        print(f"スキーマ適用中に予期せぬエラーが発生しました: {e}")
        conn.rollback()

def seed_new_master_data(conn):
    # (この関数は変更なし)
    print("--- 新規マスターデータの投入を開始します ---")
    cursor = conn.cursor()
    seed_targets = {
        "types": (TYPES_CSV_PATH, ["id", "name", "name_ja"]),
        "abilities": (ABILITIES_CSV_PATH, ["id", "name", "name_ja"]),
        "natures": (NATURES_CSV_PATH, ["id", "name", "name_ja", "increased_stat", "decreased_stat"]),
        "items": (ITEMS_CSV_PATH, ["id", "name", "name_ja"])
    }
    for table, (path, columns) in seed_targets.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            if cursor.fetchone()[0] > 0:
                print(f"テーブル '{table}' には既にデータが存在するため、スキップします。")
                continue
            print(f"'{path}' から {table} データを投入中...")
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                placeholders = ', '.join('?' * len(columns))
                cursor.executemany(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", reader)
            print(f"{table} データの投入が完了しました。")
        except sqlite3.OperationalError as e:
            print(f"エラー: テーブル '{table}' へのデータ投入に失敗しました。({e})")
        except Exception as e:
            print(f"予期せぬエラー: {e}")
    conn.commit()
    print("--- 新規マスターデータの投入が完了しました ---")

def main():
    print("ステップ1: マスターデータCSVファイルの生成を開始します。")
    generate_csv_files()
    print("マスターデータCSVファイルの生成が完了しました。")

    if not os.path.exists(DB_PATH):
        print(f"エラー: データベースファイルが見つかりません: {DB_PATH}")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        print("\nステップ2: データベーススキーマの更新を開始します。")
        apply_schema_changes(conn)
        print("\nステップ3: 新規マスターデータの投入を開始します。")
        seed_new_master_data(conn)
        print("\nすべてのデータベース更新処理が正常に完了しました。")
    except Exception as e:
        print(f"データベース処理全体でエラーが発生しました: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()
