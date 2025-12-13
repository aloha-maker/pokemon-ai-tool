import csv
import os
import sys

# 親ディレクトリをsys.pathに追加して、commonとapi_clientをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from api_client import fetch_from_pokeapi, get_all_resources, get_japanese_name
from common import MASTER_DATA_DIR, POKEMONS_CSV_PATH

def generate_pokemons_csv():
    """PokeAPIからポケモンデータを取得し、CSVファイルとして保存する"""
    print("--- ポケモンCSVファイルの生成開始 ---")
    os.makedirs(MASTER_DATA_DIR, exist_ok=True)

    try:
        with open(POKEMONS_CSV_PATH, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "name_ja", "type1", "type2", "hp", "attack", "defense", "sp_attack", "sp_defense", "speed"])
            
            pokemon_list = get_all_resources("pokemon", limit=1500)
            total = len(pokemon_list)
            
            for i, res in enumerate(pokemon_list):
                print(f"処理中: {i+1}/{total} ({res['name']})", end='\r')
                data = fetch_from_pokeapi(url=res['url'])
                if not data: continue
                
                species_data = fetch_from_pokeapi(url=data['species']['url'])
                if not species_data: continue

                name_ja = get_japanese_name(species_data)
                types = [t['type']['name'] for t in data['types']]
                stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
                
                writer.writerow([
                    data['id'], data['name'], name_ja, 
                    types[0] if len(types) > 0 else "", 
                    types[1] if len(types) > 1 else "",
                    stats.get('hp', 0), stats.get('attack', 0), stats.get('defense', 0), 
                    stats.get('special-attack', 0), stats.get('special-defense', 0), stats.get('speed', 0)
                ])
        print(f"\n'{POKEMONS_CSV_PATH}' を作成しました。")
    except Exception as e:
        print(f"\nポケモンデータの生成中にエラーが発生しました: {e}")
    finally:
        print("--- ポケモンCSVファイルの生成完了 ---")

if __name__ == '__main__':
    generate_pokemons_csv()
