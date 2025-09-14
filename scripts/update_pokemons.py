import csv
import requests
import sqlite3
import os
import time

# --- 設定項目 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "pokemon_ai.db")

# --- データ取得 ---
def fetch_from_pokeapi(endpoint=None, resource_id=None, url=None, retries=3, backoff_factor=0.5):
    """PokeAPIからデータを取得する共通関数（リトライ機能付き）"""
    if url is None:
        url = f"https://pokeapi.co/api/v2/{endpoint}/{resource_id}"
    
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"APIリクエストエラー: {e} (試行 {i + 1}/{retries})")
            if i < retries - 1:
                time.sleep(backoff_factor * (2 ** i))
            else:
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

def update_pokemon_data():
    """pokemonsテーブルのデータを最新化する"""
    print("--- ポケモンデータの更新を開始します ---")

    # 1. PokeAPIから最新のポケモンデータを取得
    all_pokemons = get_all_resources("pokemon")
    if not all_pokemons:
        print("PokeAPIからポケモンデータを取得できませんでした。処理を中断します。")
        return

    print(f"{len(all_pokemons)}匹のポケモンデータを取得しました。")
    
    pokemon_data_to_insert = []
    for pokemon_ref in all_pokemons:
        pokemon_id = pokemon_ref['url'].split('/')[-2]
        data = fetch_from_pokeapi(url=pokemon_ref['url'])
        species_data = fetch_from_pokeapi("pokemon-species", pokemon_id)
        
        if data and species_data:
            name_ja = ""
            for name_info in species_data.get('names', []):
                if name_info['language']['name'] == 'ja-Hrkt':
                    name_ja = name_info['name']
                    break

            types = [t['type']['name'] for t in data['types']]
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            row = (
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
            )
            pokemon_data_to_insert.append(row)

    # 2. データベースに接続し、データを更新
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"データベース '{DB_PATH}' に接続しました。")

        # テーブルをクリア
        cursor.execute("DELETE FROM pokemons")
        print("'pokemons' テーブルの既存データを削除しました。")

        # 新しいデータを挿入
        cursor.executemany(
            "INSERT INTO pokemons (id, name, name_ja, type1, type2, hp, attack, defense, sp_attack, sp_defense, speed) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            pokemon_data_to_insert
        )
        print(f"{len(pokemon_data_to_insert)}件のポケモンデータを'pokemons'テーブルに挿入しました。")

        conn.commit()
        print("データベースへのコミットが完了しました。")

    except sqlite3.Error as e:
        print(f"データベースエラー: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("データベース接続を閉じました。")
    
    print("--- ポケモンデータの更新が完了しました ---")


if __name__ == "__main__":
    update_pokemon_data()
