import os
import shutil
import csv

# --- 設定 ---
# 画像が格納されている元のフォルダ
SOURCE_DIR = r"C:\it-do-it-yourself-club\z_local\test\templete_match\oponent"
# コピー先のベースフォルダ
TARGET_BASE_DIR = r"C:\pokemon-ai-tool\data\pokemon_images"
# ポケモン名の対応表CSVファイル
NAME_MAPPING_CSV = r"C:\pokemon-ai-tool\data\master_data\pokemons.csv"

def setup_template_images():
    """
    指定されたディレクトリからポケモンの画像を読み込み、
    テンプレートマッチング用に名前を変換して適切なディレクトリ構造でコピーする。
    """
    print("テンプレート画像のセットアップを開始します...")

    # 1. ポケモン名の対応表を読み込む
    try:
        name_mapping = {}
        with open(NAME_MAPPING_CSV, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                # CSVの 'name' (英名) をキー、'name_ja' (日本語名) を値とする
                # キーは小文字に統一
                name_en = row.get('name', '').lower()
                name_ja = row.get('name_ja')
                if name_en and name_ja:
                    name_mapping[name_en] = name_ja
        print(f"{len(name_mapping)}件のポケモン名対応を読み込みました。")
    except FileNotFoundError:
        print(f"エラー: ポケモン名の対応表CSVが見つかりません: {NAME_MAPPING_CSV}")
        return
    except Exception as e:
        print(f"エラー: CSVファイルの読み込み中に問題が発生しました: {e}")
        return

    # 2. コピー先のベースフォルダがなければ作成
    os.makedirs(TARGET_BASE_DIR, exist_ok=True)
    print(f"コピー先のベースフォルダを確認/作成しました: {TARGET_BASE_DIR}")

    # 3. 元のフォルダから画像ファイルを取得
    if not os.path.isdir(SOURCE_DIR):
        print(f"エラー: 元のフォルダが見つかりません: {SOURCE_DIR}")
        return

    image_files = []
    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(os.path.join(root, file))

    if not image_files:
        print("元のフォルダに画像ファイルが見つかりませんでした。")
        return

    print(f"{len(image_files)}個の画像ファイルを処理します...")
    
    # 4. 各ファイルを処理
    copied_count = 0
    skipped_count = 0
    for file_path in image_files:
        try:
            # ファイル名から拡張子を除いて英名を取得し、小文字に変換
            base_name = os.path.basename(file_path)
            english_name = os.path.splitext(base_name)[0].lower()
            
            # 日本語名を取得
            japanese_name = name_mapping.get(english_name)
            
            if not japanese_name:
                print(f"警告: '{base_name}' に対応する日本語名が見つかりません。スキップします。")
                skipped_count += 1
                continue
            
            # 日本語名のフォルダパスを作成
            pokemon_dir = os.path.join(TARGET_BASE_DIR, japanese_name)
            
            # 日本語名のフォルダがなければ作成
            os.makedirs(pokemon_dir, exist_ok=True)
            
            # 画像をコピーして名前を "icon.png" に変更
            destination_path = os.path.join(pokemon_dir, "icon.png")
            shutil.copy(file_path, destination_path)
            
            print(f"コピー完了: {base_name} -> {os.path.join('data', 'pokemon_images', japanese_name, 'icon.png')}")
            copied_count += 1
        except Exception as e:
            print(f"エラー: '{file_path}' の処理中に問題が発生しました: {e}")

    print("\n--- すべての処理が完了しました ---")
    print(f"コピー成功: {copied_count}件")
    print(f"スキップ: {skipped_count}件")

if __name__ == "__main__":
    setup_template_images()
