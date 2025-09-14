import csv
import requests
import sqlite3
import os
import time

# --- 設定項目 ---
# データベースとデータファイルのパスをプロジェクトルートからの相対パスで指定
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MASTER_DATA_DIR = os.path.join(DATA_DIR, "master_data")
DB_PATH = os.path.join(DATA_DIR, "pokemon_ai.db")
SCHEMA_PATH = os.path.join(DATA_DIR, "schema.sql")
POKEMONS_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemons.csv")
MOVES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "moves.csv")

# --- データ取得 (generate_csv.py) ---
def fetch_from_pokeapi(endpoint=None, resource_id=None, url=None, retries=3, backoff_factor=0.5):
    """PokeAPIからデータを取得する共通関数（リトライ機能付き）"""
    if url is None:
        url = f"https://pokeapi.co/api/v2/{endpoint}/{resource_id}"
    
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10) # タイムアウトを設定
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            # print(f"APIリクエストエラー: {e} (試行 {i + 1}/{retries})")
            # if i < retries - 1:
            #     time.sleep(backoff_factor * (2 ** i)) # Exponential backoff
            # else:
            print(f"URLの取得に失敗しました: {url}")
            return None

def get_all_resources(endpoint):
    """指定されたエンドポイントからすべてのリソースリストを取得する"""
    results = []
    limit = 1500 if endpoint == 'pokemon' else 1200
    url = f"https://pokeapi.co/api/v2/{endpoint}?limit={limit}"
    data = fetch_from_pokeapi(url=url)
    if data:
        results.extend(data.get('results', []))
    return results


def generate_csv_files():
    """
    PokeAPIからポケモンと技のデータを取得し、CSVファイルとして保存する
    """
    print("--- CSVファイルの生成開始 ---")
    os.makedirs(MASTER_DATA_DIR, exist_ok=True)

    # ポケモンデータのCSV生成
    all_pokemons = get_all_resources("pokemon")
    print(f"ポケモンデータを取得中 ({len(all_pokemons)}匹)...")
    with open(POKEMONS_CSV_PATH, "w", newline='', encoding="utf-8") as pfile:
        pw = csv.writer(pfile)
        pw.writerow(["id", "name", "name_ja", "type1", "type2", "hp", "attack", "defense", "sp_attack", "sp_defense", "speed"])
        
        for pokemon_ref in all_pokemons:
            pokemon_id = pokemon_ref['url'].split('/')[-2]
            data = fetch_from_pokeapi(url=pokemon_ref['url'])
            species_data = fetch_from_pokeapi("pokemon-species", pokemon_id)
            
            if data and species_data:
                # 日本語名を取得
                name_ja = ""
                for name_info in species_data.get('names', []):
                    if name_info['language']['name'] == 'ja-Hrkt':
                        name_ja = name_info['name']
                        break

                types = [t['type']['name'] for t in data['types']]
                stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                row = [
                    data['id'],
                    data['name'],
                    name_ja,
                    types[0] if len(types) > 0 else "",
                    types[1] if len(types) > 1 else "",
                    stats.get('hp'),
                    stats.get('attack'),
                    stats.get('defense'),
                    stats.get('special-attack'),
                    stats.get('special-defense'),
                    stats.get('speed'),
                ]
                pw.writerow(row)
    print(f"'{POKEMONS_CSV_PATH}' を作成しました。")

    # 技データのCSV生成
    all_moves = get_all_resources("move")
    print(f"技データを取得中 ({len(all_moves)}個)...")
    with open(MOVES_CSV_PATH, "w", newline='', encoding="utf-8") as mfile:
        mw = csv.writer(mfile)
        mw.writerow(["id", "name", "type", "category", "power", "accuracy"])
        for move_ref in all_moves:
            data = fetch_from_pokeapi(url=move_ref['url'])
            if data:
                mw.writerow([
                    data['id'],
                    data['name'],
                    data['type']['name'],
                    data['damage_class']['name'],
                    data.get('power'),
                    data.get('accuracy'),
                ])
    print(f"'{MOVES_CSV_PATH}' を作成しました。")
    print("--- CSVファイルの生成完了 ---")


# --- データベース初期化 (init_db.py) ---
def initialize_database():
    """
    データベースファイルを初期化し、スキーマに基づいてテーブルを作成する
    """
    print("--- データベースの初期化開始 ---")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"既存のデータベース '{DB_PATH}' を削除しました。")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"データベース '{DB_PATH}' を作成し、接続しました。")

        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            cursor.executescript(sql_script)

        conn.commit()
        print("テーブルの作成が完了しました。")
        return conn
    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
        return None
    finally:
        print("--- データベースの初期化完了 ---")


# --- データ投入 (seed_db.py) ---
def seed_data(conn):
    """
    CSVファイルからデータを読み込み、データベースに投入する
    """
    print("--- データベースへのデータ投入開始 ---")
    if not conn:
        print("エラー: データベース接続がありません。")
        return

    cursor = conn.cursor()
    try:
        # ポケモンデータの投入
        print(f"'{POKEMONS_CSV_PATH}' からポケモンデータを投入中...")
        with open(POKEMONS_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ
            cursor.executemany(
                "INSERT INTO pokemons (id, name, name_ja, type1, type2, hp, attack, defense, sp_attack, sp_defense, speed) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                reader
            )
        print("ポケモンデータの投入が完了しました。")

        # 技データの投入
        print(f"'{MOVES_CSV_PATH}' から技データを投入中...")
        with open(MOVES_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # ヘッダーをスキップ
            cursor.executemany(
                "INSERT INTO moves (id, name, type, category, power, accuracy) VALUES (?, ?, ?, ?, ?, ?)",
                reader
            )
        print("技データの投入が完了しました。")

        conn.commit()
        print("データベースへのコミットが完了しました。")
    except Exception as e:
        print(f"データ投入中にエラーが発生しました: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("データベース接続を閉じました。")
        print("--- データベースへのデータ投入完了 ---")


# --- メイン処理 ---
def main():
    """
    一連のデータベースセットアップ処理を実行する
    """
    # 1. CSVファイルを生成
    generate_csv_files()

    # 2. データベースを初期化
    conn = initialize_database()

    # 3. データベースにデータを投入
    if conn:
        seed_data(conn)

    print("データベースのセットアップがすべて完了しました。")

if __name__ == '__main__':
    main()
