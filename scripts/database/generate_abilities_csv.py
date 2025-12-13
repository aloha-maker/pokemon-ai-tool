import csv
import os
import sys

# 親ディレクトリをsys.pathに追加して、commonとapi_clientをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from api_client import fetch_from_pokeapi, get_all_resources, get_japanese_name
from common import MASTER_DATA_DIR, ABILITIES_CSV_PATH

def generate_abilities_csv():
    """PokeAPIから特性データを取得し、CSVファイルとして保存する"""
    print("--- 特性CSVファイルの生成開始 ---")
    os.makedirs(MASTER_DATA_DIR, exist_ok=True)
    endpoint = "ability"
    path = ABILITIES_CSV_PATH
    header = ["id", "name", "name_ja"]

    try:
        with open(path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            
            resource_list = get_all_resources(endpoint)
            total = len(resource_list)
            processed_names = set()

            for i, res in enumerate(resource_list):
                print(f"処理中: {i+1}/{total} ({res['name']})", end='\r')
                data = fetch_from_pokeapi(url=res['url'])
                if not data: continue
                
                item_name = data['name']
                if item_name in processed_names:
                    continue
                processed_names.add(item_name)

                writer.writerow([data['id'], item_name, get_japanese_name(data)])
        print(f"\n'{path}' を作成しました。")
    except Exception as e:
        print(f"\n特性データの生成中にエラーが発生しました: {e}")
    finally:
        print("--- 特性CSVファイルの生成完了 ---")

if __name__ == '__main__':
    generate_abilities_csv()
