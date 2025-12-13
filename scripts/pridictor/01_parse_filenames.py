import os
import re
import csv
from typing import Dict, Optional, List

def parse_filename(filename: str) -> Optional[Dict[str, any]]:
    """
    指定されたルールのファイル名を解析し、情報を辞書として返します。
    ルール: '{short_hash}_{roi_name}_{frame_idx:06d}.gt.txt'

    Args:
        filename (str): 解析対象のファイル名。

    Returns:
        Optional[Dict[str, any]]: 抽出した情報を含む辞書。
                                   パターンに一致しない場合はNoneを返します。
    """
    pattern = re.compile(r"^([^_]+)_(.+)_(\d{6})\.gt\.txt$")
    
    match = pattern.match(filename)
    
    if match:
        short_hash, roi_name, frame_idx_str = match.groups()
        
        return {
            'short_hash': short_hash,
            'roi_name': roi_name,
            'frame_idx': int(frame_idx_str)
        }
    
    return None

def process_directory(directory_path: str) -> List[Dict[str, any]]:
    """
    指定されたディレクトリ内の全ファイルを再帰的に処理し、解析結果のリストを返します。

    Args:
        directory_path (str): ファイルが格納されているディレクトリのパス。

    Returns:
        List[Dict[str, any]]: 各ファイルの解析結果を格納した辞書のリスト。
    """
    if not os.path.isdir(directory_path):
        print(f"エラー: ディレクトリ '{directory_path}' が見つかりません。")
        return []
    
    parsed_data_list = []
    
    # サブフォルダを含めて再帰的に検索
    for root, dirs, files in os.walk(directory_path):
        for filename in sorted(files):
            parsed_info = parse_filename(filename)
            
            if parsed_info:
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ocr_text = f.read()
                    
                    parsed_info['ocr_text'] = ocr_text
                    parsed_info['file_path'] = file_path
                    parsed_data_list.append(parsed_info)
                    
                except Exception as e:
                    # エラーが発生してもスキップして続行
                    pass
            
    return parsed_data_list

def save_to_csv(data_list: List[Dict[str, any]], output_path: str):
    """
    解析結果をCSVファイルに保存します。

    Args:
        data_list (List[Dict[str, any]]): 解析結果のリスト。
        output_path (str): 出力するCSVファイルのパス。
    """
    if not data_list:
        print("保存するデータがありません。")
        return
    
    fieldnames = ['short_hash', 'roi_name', 'frame_idx', 'ocr_text', 'file_path']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_list)

# --- スクリプト実行デモ ---
if __name__ == '__main__':
    # 実際のディレクトリパスを指定してください
    target_directory = input("処理するディレクトリのパスを入力してください: ")
    
    # 指定されたフォルダを対象に処理を実行
    results = process_directory(target_directory)
    
    if results:
        # CSV出力パスを設定（入力ディレクトリと同じ場所）
        csv_output_path = os.path.join(target_directory, "parsed_results.csv")
        save_to_csv(results, csv_output_path)
        
        print(f"処理完了: {len(results)}件のファイルを解析しました。")
        print(f"CSV出力: {csv_output_path}")
    else:
        print("有効なファイルが見つかりませんでした。")