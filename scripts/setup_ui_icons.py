import os
import shutil

# --- 設定 ---
# テンプレート画像が格納されているベースフォルダ
SOURCE_BASE_DIR = os.path.join("data", "pokemon_images")
# UI用アイコンのコピー先フォルダ
TARGET_DIR = os.path.join("static", "pokemon_icons")

def create_ui_icons():
    """
    テンプレートマッチング用の画像から、UI表示用のアイコン画像を生成する。
    data/pokemon_images/日本語名/icon.png -> static/pokemon_icons/日本語名.png
    """
    print("UI用アイコンのセットアップを開始します...")

    # 1. ソースディレクトリの存在チェック
    if not os.path.isdir(SOURCE_BASE_DIR):
        print(f"エラー: ソースディレクトリが見つかりません: {SOURCE_BASE_DIR}")
        return

    # 2. ターゲットディレクトリを作成
    os.makedirs(TARGET_DIR, exist_ok=True)
    print(f"アイコンのコピー先: {TARGET_DIR}")

    # 3. 各ポケモンのディレクトリを走査
    try:
        pokemon_dirs = [d for d in os.listdir(SOURCE_BASE_DIR) if os.path.isdir(os.path.join(SOURCE_BASE_DIR, d))]
    except FileNotFoundError:
        print(f"エラー: ソースディレクトリにアクセスできません: {SOURCE_BASE_DIR}")
        return
        
    if not pokemon_dirs:
        print(f"ソースディレクトリ '{SOURCE_BASE_DIR}' にポケモンのフォルダが見つかりませんでした。")
        return

    print(f"{len(pokemon_dirs)}個のポケモンを処理します...")
    copied_count = 0
    skipped_count = 0
    
    for pokemon_name in pokemon_dirs:
        source_pokemon_dir = os.path.join(SOURCE_BASE_DIR, pokemon_name)
        
        # フォルダ内の画像ファイルを探す
        image_files = [f for f in os.listdir(source_pokemon_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print(f"警告: '{pokemon_name}' のフォルダに画像ファイルが見つかりません。スキップします。")
            skipped_count += 1
            continue

        # 最初の画像をソースとして使用
        source_image_path = os.path.join(source_pokemon_dir, image_files[0])
        
        # ターゲットのファイルパスを生成 (例: static/pokemon_icons/カイリュー.png)
        target_image_path = os.path.join(TARGET_DIR, f"{pokemon_name}.png")
        
        try:
            shutil.copy(source_image_path, target_image_path)
            # print(f"コピー完了: {pokemon_name}.png") # ログが長くなるのでコメントアウト
            copied_count += 1
        except Exception as e:
            print(f"エラー: '{source_image_path}' のコピー中に問題が発生しました: {e}")
            skipped_count += 1

    print("\n--- すべての処理が完了しました ---")
    print(f"コピー成功: {copied_count}件")
    print(f"スキップ: {skipped_count}件")

if __name__ == "__main__":
    create_ui_icons()
