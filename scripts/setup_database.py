import csv
import requests
import sqlite3
import os
import time

# --- 設定項目 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MASTER_DATA_DIR = os.path.join(DATA_DIR, "master_data")
DB_PATH = os.path.join(DATA_DIR, "pokemon_ai.db")
SCHEMA_PATH = os.path.join(DATA_DIR, "schema.sql")

# CSVファイルのパス
POKEMONS_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemons.csv")
MOVES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "moves.csv")
TYPES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "types.csv")
ABILITIES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "abilities.csv")
NATURES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "natures.csv")
ITEMS_CSV_PATH = os.path.join(MASTER_DATA_DIR, "items.csv")


# --- データ取得 ---
def fetch_from_pokeapi(endpoint=None, resource_id=None, url=None, retries=3, backoff_factor=0.5):
    """PokeAPIからデータを取得する共通関数"""
    if url is None:
        url = f"https://pokeapi.co/api/v2/{endpoint}/{resource_id}"
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if i == retries - 1:
                print(f"URLの取得に失敗しました: {url}")
            time.sleep(backoff_factor * (2 ** i))
    return None

def get_all_resources(endpoint, limit=2000):
    """指定されたエンドポイントからすべてのリソースリストを取得する"""
    url = f"https://pokeapi.co/api/v2/{endpoint}?limit={limit}"
    data = fetch_from_pokeapi(url=url)
    return data.get('results', []) if data else []

def get_japanese_name(data):
    """データから日本語名を取得する"""
    for name_info in data.get('names', []):
        if name_info['language']['name'] == 'ja-Hrkt':
            return name_info['name']
    return ""

def generate_csv_files():
    """PokeAPIから各種マスターデータを取得し、CSVファイルとして保存する"""
    print("--- CSVファイルの生成開始 ---")
    os.makedirs(MASTER_DATA_DIR, exist_ok=True)

    # ポケモンデータ
    print("ポケモンデータを取得中...")
    with open(POKEMONS_CSV_PATH, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "name_ja", "type1", "type2", "hp", "attack", "defense", "sp_attack", "sp_defense", "speed"])
        for res in get_all_resources("pokemon", limit=1500):
            data = fetch_from_pokeapi(url=res['url'])
            if not data: continue
            species_data = fetch_from_pokeapi(url=data['species']['url'])
            name_ja = get_japanese_name(species_data)
            types = [t['type']['name'] for t in data['types']]
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            writer.writerow([data['id'], data['name'], name_ja, types[0], types[1] if len(types) > 1 else "",
                               stats['hp'], stats['attack'], stats['defense'], 
                               stats['special-attack'], stats['special-defense'], stats['speed']])
    print(f"'{POKEMONS_CSV_PATH}' を作成しました。")

    # 技データ
    print("技データを取得中...")
    with open(MOVES_CSV_PATH, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "name_ja", "type", "category", "power", "accuracy"])
        for res in get_all_resources("move"):
            data = fetch_from_pokeapi(url=res['url'])
            if not data: continue
            writer.writerow([data['id'], data['name'], get_japanese_name(data), data['type']['name'],
                               data['damage_class']['name'], data.get('power'), data.get('accuracy')])
    print(f"'{MOVES_CSV_PATH}' を作成しました。")

    # タイプ、特性、性格、持ち物データ
    endpoints = {
        "type": (TYPES_CSV_PATH, ["id", "name", "name_ja"]),
        "ability": (ABILITIES_CSV_PATH, ["id", "name", "name_ja"]),
        "nature": (NATURES_CSV_PATH, ["id", "name", "name_ja", "increased_stat", "decreased_stat"]),
        "item": (ITEMS_CSV_PATH, ["id", "name", "name_ja"])
    }
    for endpoint, (path, header) in endpoints.items():
        print(f"{endpoint}データを取得中...")
        with open(path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            processed_names = set() # 重複チェック用
            for res in get_all_resources(endpoint):
                data = fetch_from_pokeapi(url=res['url'])
                if not data: continue
                
                # 英語名で重複をチェック
                item_name = data['name']
                if item_name in processed_names:
                    continue
                processed_names.add(item_name)

                row = [data['id'], item_name, get_japanese_name(data)]
                if endpoint == 'nature':
                    inc_stat = data['increased_stat']['name'] if data['increased_stat'] else ''
                    dec_stat = data['decreased_stat']['name'] if data['decreased_stat'] else ''
                    row.extend([inc_stat, dec_stat])
                writer.writerow(row)
        print(f"'{path}' を作成しました。")

    print("--- CSVファイルの生成完了 ---")


# --- データベース初期化 ---
def initialize_database():
    """データベースファイルを初期化し、スキーマに基づいてテーブルを作成する"""
    print("--- データベースの初期化開始 ---")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"既存のデータベース '{DB_PATH}' を削除しました。")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"データベース '{DB_PATH}' を作成し、接続しました。")
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            cursor.executescript(f.read())
        conn.commit()
        print("テーブルの作成が完了しました。")
        return conn
    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
        return None
    finally:
        print("--- データベースの初期化完了 ---")


# --- データ投入 ---
def seed_data(conn):
    """CSVファイルからデータを読み込み、データベースに投入する"""
    print("--- データベースへのデータ投入開始 ---")
    if not conn: return
    cursor = conn.cursor()
    try:
        def seed_from_csv(path, table, columns):
            print(f"'{path}' から {table} データを投入中...")
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーをスキップ
                placeholders = ', '.join('?' * len(columns))
                cursor.executemany(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", reader)
            print(f"{table} データの投入が完了しました。")

        seed_from_csv(POKEMONS_CSV_PATH, "pokemons", ["id", "name", "name_ja", "type1", "type2", "hp", "attack", "defense", "sp_attack", "sp_defense", "speed"])
        seed_from_csv(MOVES_CSV_PATH, "moves", ["id", "name", "name_ja", "type", "category", "power", "accuracy"])
        seed_from_csv(TYPES_CSV_PATH, "types", ["id", "name", "name_ja"])
        seed_from_csv(ABILITIES_CSV_PATH, "abilities", ["id", "name", "name_ja"])
        seed_from_csv(NATURES_CSV_PATH, "natures", ["id", "name", "name_ja", "increased_stat", "decreased_stat"])
        seed_from_csv(ITEMS_CSV_PATH, "items", ["id", "name", "name_ja"])

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
    """一連のデータベースセットアップ処理を実行する"""
    generate_csv_files()
    conn = initialize_database()
    if conn:
        seed_data(conn)
    print("データベースのセットアップがすべて完了しました。")

if __name__ == '__main__':
    main()