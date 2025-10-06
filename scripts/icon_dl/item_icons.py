import os
import requests
import time

# 保存フォルダ
save_dir = "pokemon_item_icons"
os.makedirs(save_dir, exist_ok=True)

# 全アイテム一覧を取得
base_url = "https://pokeapi.co/api/v2/item?limit=2000"
response = requests.get(base_url)
items = response.json()["results"]

for item in items:
    name_en = item["name"]
    item_data = requests.get(item["url"]).json()

    # スプライトURL取得
    sprite_url = item_data["sprites"]["default"]
    if not sprite_url:
        continue  # 画像がないアイテムはスキップ

    # 保存パス（英名ファイル）
    save_path = os.path.join(save_dir, f"{name_en}.png")

    try:
        img_data = requests.get(sprite_url).content
        with open(save_path, "wb") as f:
            f.write(img_data)
        print(f"✅ {name_en}.png 保存完了")
    except Exception as e:
        print(f"⚠️ {name_en} ダウンロード失敗: {e}")

    # サーバー負荷軽減のため少し待つ
    time.sleep(0.1)
