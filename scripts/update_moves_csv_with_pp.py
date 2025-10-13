import requests
import csv
import os
import time

# --- 設定 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_DATA_DIR = os.path.join(BASE_DIR, "data", "master_data")
INPUT_CSV_PATH = os.path.join(MASTER_DATA_DIR, "moves.csv")
OUTPUT_CSV_PATH = os.path.join(MASTER_DATA_DIR, "moves_updated.csv") # 元ファイルを上書きしない
POKEAPI_MOVE_URL = "https://pokeapi.co/api/v2/move/{}"

# --- メイン処理 ---
def main():
    """
    既存のmoves.csvを読み込み、PokeAPIから各技のPPを取得して、
    PPカラムを追加した新しいCSVファイル (moves_updated.csv) を生成する。
    """
    print("--- moves.csv の更新を開始します ---")

    # 元のCSVファイルを読み込む
    try:
        with open(INPUT_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            original_data = list(reader)
    except FileNotFoundError:
        print(f"エラー: {INPUT_CSV_PATH} が見つかりません。")
        return

    header = original_data[0]
    rows = original_data[1:]

    # ヘッダーに 'pp' がなければ追加
    if 'pp' not in header:
        header.append('pp')
    
    # カラムのインデックスを取得
    try:
        name_index = header.index('name') # 英語名カラムのインデックス
    except ValueError:
        print("エラー: CSVヘッダーに 'name' カラムが見つかりません。")
        return

    updated_rows = []
    total_moves = len(rows)

    print(f"合計 {total_moves} 件の技データを更新します。")

    # 各技についてAPIからPPを取得
    for i, row in enumerate(rows):
        # 空の行はスキップ
        if not row:
            continue

        move_name = row[name_index]
        
        # PokeAPIでは技名がハイフン区切りになっている
        api_move_name = move_name.replace('_', '-')

        print(f"({i+1}/{total_moves}) 技 '{move_name}' のPPを取得中...")

        try:
            response = requests.get(POKEAPI_MOVE_URL.format(api_move_name), timeout=10)
            response.raise_for_status()  # 200番台以外のステータスコードで例外を発生
            
            api_data = response.json()
            pp = api_data.get('pp', 0) # PPが取得できなければ0

        except requests.exceptions.RequestException as e:
            print(f"  -> 警告: APIリクエストに失敗しました ({e})。'{move_name}' のPPは 0 に設定します。")
            pp = 0
        
        # 新しい行を作成（元の行の長さを超えるインデックスに対応）
        new_row = list(row)
        while len(new_row) < len(header):
            new_row.append('')
        new_row[header.index('pp')] = pp

        updated_rows.append(new_row)
        
        # APIへの負荷を考慮して少し待機
        time.sleep(0.05)

    # 更新された内容を新しいCSVファイルに書き込む
    try:
        with open(OUTPUT_CSV_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(updated_rows)
        print(f"\n更新が完了しました。新しいファイル: {OUTPUT_CSV_PATH}")
        print(f"確認後、手動で {INPUT_CSV_PATH} を {OUTPUT_CSV_PATH} の内容で上書きしてください。")
    except IOError as e:
        print(f"エラー: ファイルの書き込みに失敗しました ({e})")

if __name__ == '__main__':
    main()
