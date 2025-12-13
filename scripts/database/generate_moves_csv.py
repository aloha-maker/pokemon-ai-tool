import csv
import os
import sys

# 親ディレクトリをsys.pathに追加して、commonとapi_clientをインポート可能にする
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from api_client import fetch_from_pokeapi, get_all_resources, get_japanese_name
from common import MASTER_DATA_DIR, MOVES_CSV_PATH

def generate_moves_csv():
    """PokeAPIから技データを取得し、CSVファイルとして保存する"""
    print("--- 技CSVファイルの生成開始 ---")
    os.makedirs(MASTER_DATA_DIR, exist_ok=True)

    try:
        with open(MOVES_CSV_PATH, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            # データベースのスキーマに合わせてppも取得
            writer.writerow(["id", "name", "name_ja", "type", "category", "power", "accuracy", "pp"])
            
            move_list = get_all_resources("move")
            total = len(move_list)

            for i, res in enumerate(move_list):
                print(f"処理中: {i+1}/{total} ({res['name']})", end='\r')
                data = fetch_from_pokeapi(url=res['url'])
                if not data: continue
                
                writer.writerow([
                    data['id'], data['name'], get_japanese_name(data), 
                    data['type']['name'], data['damage_class']['name'], 
                    data.get('power'), data.get('accuracy'), data.get('pp')
                ])
        print(f"\n'{MOVES_CSV_PATH}' を作成しました。")
    except Exception as e:
        print(f"\n技データの生成中にエラーが発生しました: {e}")
    finally:
        print("--- 技CSVファイルの生成完了 ---")

if __name__ == '__main__':
    generate_moves_csv()
