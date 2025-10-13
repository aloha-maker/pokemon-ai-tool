import requests
import time
import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.manager import DatabaseManager

POKEAPI_POKEMON_URL = "https://pokeapi.co/api/v2/pokemon/{}"

def main():
    """
    PokeAPIから各ポケモンの特性情報を取得し、pokemon_abilitiesテーブルに格納する。
    このスクリプトは、reseed_database.pyで各種マスターデータが投入された後に実行することを想定している。
    """
    print("--- ポケモン-特性 紐付けデータの投入を開始します ---")
    db_manager = DatabaseManager()

    try:
        with db_manager as db:
            # 1. 必要なマスターデータを取得してキャッシュ
            print("データベースからポケモンと特性のマスターデータを取得中...")
            pokemons = db.get_master_data_by_resource('pokemons')
            abilities = db.get_master_data_by_resource('abilities')
            
            # 高速アクセスのために名前をキーにした辞書を作成
            pokemon_map = {p['name']: p['id'] for p in pokemons}
            ability_map = {a['name']: a['id'] for a in abilities}
            print("マスターデータの準備が完了しました。")

            all_pokemon_abilities = []
            total_pokemons = len(pokemons)

            # 2. 各ポケモンについてAPIから特性情報を取得
            for i, pokemon in enumerate(pokemons):
                pokemon_name_api = pokemon['name'].lower() # APIは小文字
                pokemon_id_db = pokemon['id']

                print(f"({i+1}/{total_pokemons}) {pokemon['name_ja']} ({pokemon_name_api}) の特性情報を取得中...")

                try:
                    response = requests.get(POKEAPI_POKEMON_URL.format(pokemon_name_api), timeout=10)
                    
                    # 404 Not Foundの場合はスキップ
                    if response.status_code == 404:
                        print(f"  -> 警告: PokeAPIに {pokemon_name_api} が見つかりませんでした。スキップします。")
                        continue
                    
                    response.raise_for_status() # その他のエラーは例外を発生
                    api_data = response.json()

                    # 3. 取得した特性を処理
                    for ability_info in api_data.get('abilities', []):
                        ability_name_api = ability_info['ability']['name']
                        is_hidden = ability_info['is_hidden']
                        
                        # キャッシュした特性マスタからIDを引く
                        if ability_name_api in ability_map:
                            ability_id_db = ability_map[ability_name_api]
                            all_pokemon_abilities.append((pokemon_id_db, ability_id_db, 1 if is_hidden else 0))
                        else:
                            print(f"  -> 警告: 特性 '{ability_name_api}' がDBマスターに存在しません。")

                except requests.exceptions.RequestException as e:
                    print(f"  -> エラー: {pokemon_name_api} のAPIリクエストに失敗しました: {e}")
                
                # APIへの負荷軽減
                time.sleep(0.05)

            # 4. データベースに一括挿入
            if all_pokemon_abilities:
                print(f"\n取得した {len(all_pokemon_abilities)} 件の紐付けデータをデータベースに挿入します...")
                cursor = db.get_cursor()
                cursor.executemany(
                    "INSERT OR IGNORE INTO pokemon_abilities (pokemon_id, ability_id, is_hidden) VALUES (?, ?, ?)",
                    all_pokemon_abilities
                )
                db.conn.commit()
                print("データの挿入が完了しました。")
            else:
                print("\nデータベースに挿入するデータがありませんでした。")

    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")
    finally:
        print("--- ポケモン-特性 紐付けデータの投入を終了します ---")

if __name__ == '__main__':
    main()
