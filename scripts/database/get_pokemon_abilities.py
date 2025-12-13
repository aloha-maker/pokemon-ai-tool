import requests
import pandas as pd
import argparse
import os
import time

def get_pokemon_abilities(pokemon_id):
    """
    PokeAPIから指定されたポケモンの覚える特性IDのリストを取得する
    """
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        pokemon_data = response.json()
        # 'abilities' フィールドから特性IDを抽出
        ability_ids = {int(ability_info['ability']['url'].strip('/').split('/')[-1]) for ability_info in pokemon_data['abilities']}
        return sorted(list(ability_ids))
    except requests.exceptions.RequestException as e:
        if e.response and e.response.status_code == 404:
            print(f"\n警告: ポケモンID {pokemon_id} はPokeAPIに見つかりませんでした。スキップします。")
            return None
        print(f"\nポケモンID {pokemon_id} のデータ取得中にエラーが発生しました: {e}")
        return None

def main():
    """
    コマンドラインからポケモンIDを受け取り、覚える特性リストをCSVに出力する
    """
    parser = argparse.ArgumentParser(
        description='指定されたポケモンID、またはpokemons.csv内の全ポケモンの覚える特性リストをPokeAPIから取得し、CSVファイルに出力します。',
    )
    parser.add_argument(
        '--pokemon_id', '-p',
        type=int,
        help='特性リストを取得したい単体のポケモンID。これを指定すると、入力ファイルは無視されます。'
    )
    parser.add_argument(
        '--input', '-i', 
        default='data/master_data/pokemons.csv', 
        help='全件取得の際に使用するpokemons.csvのパス。'
    )
    parser.add_argument(
        '--output', '-o', 
        default='pokemon_abilities.csv', 
        help='出力するCSVファイル名。デフォルトは pokemon_abilities.csv です。'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.1,
        help='各APIリクエスト間の遅延（秒）。'
    )
    
    args = parser.parse_args()
    
    output_dir = 'data/master_data'
    os.makedirs(output_dir, exist_ok=True)
    output_filepath = os.path.join(output_dir, args.output)

    delay = args.delay
    results = []

    if args.pokemon_id:
        pokemon_id = args.pokemon_id
        print(f"ポケモンID: {pokemon_id} の特性リストを取得しています...")
        abilities = get_pokemon_abilities(pokemon_id)
        if abilities:
            results.append({
                'pokemon_id': pokemon_id,
                'ability_ids': ','.join(map(str, abilities))
            })
        else:
            print(f"ポケモンID: {pokemon_id} の特性リストを取得できませんでした。")
    else:
        input_filename = args.input
        if not os.path.exists(input_filename):
            print(f"エラー: 入力ファイル '{input_filename}' が見つかりません。")
            return

        try:
            pokemon_df = pd.read_csv(input_filename)
            pokemon_ids = pokemon_df['id'].tolist()
        except Exception as e:
            print(f"エラー: '{input_filename}' の読み込み中にエラーが発生しました: {e}")
            return

        print(f"'{input_filename}' から {len(pokemon_ids)} 件のポケモンIDを検出しました。")
        print(f"特性データの取得を開始します...（完了まで数分かかる場合があります）")

        for i, pokemon_id in enumerate(pokemon_ids):
            print(f"処理中: {i+1}/{len(pokemon_ids)} (ID: {pokemon_id})", end='\r')
            abilities = get_pokemon_abilities(pokemon_id)
            if abilities:
                results.append({
                    'pokemon_id': pokemon_id,
                    'ability_ids': ','.join(map(str, abilities))
                })
            time.sleep(delay)
        print("\n")

    if results:
        try:
            df = pd.DataFrame(results)
            df.to_csv(output_filepath, index=False, encoding='utf-8')
            print(f"処理が完了しました。")
            print(f"結果を '{os.path.abspath(output_filepath)}' に保存しました。")
        except IOError as e:
            print(f"\nファイル書き込みエラー: {e}")
    else:
        if not args.pokemon_id:
             print("取得できたデータがありませんでした。")

if __name__ == '__main__':
    main()
