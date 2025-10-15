import csv
import os
import sys

# 親ディレクトリをsys.pathに追加して、commonとapi_clientをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from api_client import fetch_from_pokeapi, get_all_resources, get_japanese_name
from common import MASTER_DATA_DIR, ITEMS_CSV_PATH

def generate_items_csv():
    """PokeAPIから道具データを取得し、CSVファイルとして保存する"""
    print("--- 道具CSVファイルの生成開始 ---")
    os.makedirs(MASTER_DATA_DIR, exist_ok=True)

    try:
        with open(ITEMS_CSV_PATH, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "name_ja"])
            
            item_list = get_all_resources("item")
            total = len(item_list)
            processed_names = set() # 重複チェック用

            for i, res in enumerate(item_list):
                print(f"処理中: {i+1}/{total} ({res['name']})", end='\r')
                data = fetch_from_pokeapi(url=res['url'])
                if not data: continue
                
                # 英語名で重複をチェック (APIに重複データが存在するため)
                item_name = data['name']
                if item_name in processed_names:
                    continue
                processed_names.add(item_name)

                writer.writerow([data['id'], item_name, get_japanese_name(data)])
        print(f"\n'{ITEMS_CSV_PATH}' を作成しました。")
    except Exception as e:
        print(f"\n道具データの生成中にエラーが発生しました: {e}")
    finally:
        print("--- 道具CSVファイルの生成完了 ---")

if __name__ == '__main__':
    generate_items_csv()
