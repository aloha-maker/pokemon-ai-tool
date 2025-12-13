import pandas as pd
import os

def reshape_csv_data(csv_file_path):
    """
    縦型のCSVデータを横型に変換
    """
    df = pd.read_csv(csv_file_path)
    
    # フレーム番号ごとにデータを集約
    frames = df['frame_idx'].unique()
    reshaped_data = []
    
    for frame in frames:
        frame_data = {'frame': frame}
        frame_rows = df[df['frame_idx'] == frame]
        
        for _, row in frame_rows.iterrows():
            roi_name = row['roi_name']
            ocr_text = row['ocr_text']
            frame_data[roi_name] = ocr_text
        
        reshaped_data.append(frame_data)
    
    return pd.DataFrame(reshaped_data)

def separate_turns_and_export(csv_file_path, pokemon_column='my_pokemon_name'):
    """
    my_pokemon_nameが存在するフレームをターン開始として分別し、指定フォーマットで出力
    """
    # データ構造を変換
    df = reshape_csv_data(csv_file_path)
    
    # 出力ファイル名の設定
    input_dir = os.path.dirname(csv_file_path)
    input_filename = os.path.splitext(os.path.basename(csv_file_path))[0]
    output_file_path = os.path.join(input_dir, f"{input_filename}_output.txt")
    
    # フレーム番号でソート
    df = df.sort_values('frame')
    
    # バトル基本情報を事前に取得（最初に見つかったものを使用）
    battle_info_frame = None
    for _, row in df.iterrows():
        if 'battle_id' in row and pd.notna(row['battle_id']):
            battle_info_frame = row
            break
    
    turns = []
    current_turn = []
    
    # ターン分別 - シンプルな方法
    for index, row in df.iterrows():
        has_pokemon = (pokemon_column in row and 
                      pd.notna(row[pokemon_column]) and 
                      str(row[pokemon_column]).strip() != '')
        
        # ポケモン名がある場合は新しいターンの開始
        if has_pokemon and current_turn:
            turns.append(current_turn)
            current_turn = [row]
        else:
            current_turn.append(row)
    
    if current_turn:
        turns.append(current_turn)
    
    print(f"デバッグ: 合計 {len(turns)} ターン検出")
    
    # テキストファイルに出力
    with open(output_file_path, 'w', encoding='utf-8') as f:
        # バトル基本情報を最初に出力
        if battle_info_frame is not None:
            frame_num = format_value(battle_info_frame.get('frame', ''))
            battle_id = format_value(battle_info_frame.get('battle_id', ''))
            select = format_value(battle_info_frame.get('select', ''))
            opponent_name = format_value(battle_info_frame.get('opponent_name', ''))
            f.write(f"{frame_num}：\t{battle_id}：{select}：{opponent_name}\n\n")
        
        # 各ターンを処理
        for turn_idx, turn_frames in enumerate(turns):
            # ターン内のデータをフレーム番号でソート
            turn_frames = sorted(turn_frames, key=lambda x: x['frame'])
            
            # ターン内のポケモン情報フレームを抽出
            pokemon_frames = [f for f in turn_frames if format_value(f.get(pokemon_column, '')).strip()]
            
            # ターン内の特性・コメントフレームを抽出
            comment_frames = [f for f in turn_frames if not format_value(f.get(pokemon_column, '')).strip()]
            
            # ターン表示（ポケモンがいる場合のみターン番号を表示）
            if pokemon_frames:
                first_pokemon_frame = pokemon_frames[0]
                frame_num = format_value(first_pokemon_frame.get('frame', ''))
                
                # 0ターン目かどうかを判定
                if turn_idx == 0 and frame_num == "4374":
                    f.write("0ターン目：\n")
                else:
                    f.write(f"{frame_num}：\t{turn_idx}ターン目：\n")
                
                # ポケモン情報を出力
                for pokemon_frame in pokemon_frames:
                    frame_num = format_value(pokemon_frame.get('frame', ''))
                    my_pokemon = format_value(pokemon_frame.get(pokemon_column, ''))
                    my_hp = format_value(pokemon_frame.get('my_pokemon_hp', ''))
                    my_ailment = format_value(pokemon_frame.get('my_ailment', ''))
                    opponent_pokemon = format_value(pokemon_frame.get('opponent_pokemon_name', ''))
                    opponent_hp = format_value(pokemon_frame.get('opponent_pokemon_hp', ''))
                    your_ailment = format_value(pokemon_frame.get('your_ailment', ''))
                    
                    f.write(f"{frame_num}：\t　自分：{my_pokemon} HP{my_hp}％ {my_ailment}\n")
                    f.write(f"{frame_num}：\t　相手：{opponent_pokemon} HP{opponent_hp}％ {your_ailment}\n")
            
            # 特性とコメントを出力（フレーム番号順に）
            for comment_frame in comment_frames:
                frame_num = format_value(comment_frame.get('frame', ''))
                
                # 0ターン目の場合は特別処理
                if turn_idx == 0 and frame_num in ["5000", "5001"]:
                    live_comment1 = format_value(comment_frame.get('live_comment_row1', ''))
                    live_comment2 = format_value(comment_frame.get('live_comment_row2', ''))
                    combined_text = f"{live_comment1}{live_comment2}"
                else:
                    # 通常の特性・コメント処理
                    my_tokusei1 = format_value(comment_frame.get('my_tokusei_row1', ''))
                    my_tokusei2 = format_value(comment_frame.get('my_tokusei_row2', ''))
                    your_tokusei1 = format_value(comment_frame.get('your_tokusei_row1', ''))
                    your_tokusei2 = format_value(comment_frame.get('your_tokusei_row2', ''))
                    live_comment1 = format_value(comment_frame.get('live_comment_row1', ''))
                    live_comment2 = format_value(comment_frame.get('live_comment_row2', ''))
                    combined_text = f"{my_tokusei1}{my_tokusei2}{your_tokusei1}{your_tokusei2}{live_comment1}{live_comment2}"
                
                if combined_text.strip():
                    f.write(f"{frame_num}：\t　　{combined_text}\n")
            
            # ターン区切り
            if turn_idx < len(turns) - 1:
                f.write("\n")
    
    print(f"処理完了: {output_file_path} に出力されました")

def format_value(value):
    """値を安全にフォーマット"""
    if pd.isna(value) or value is None:
        return ''
    return str(value)

# 使用例
if __name__ == "__main__":
    # ここで処理したいCSVファイルのパスを指定
    csv_file_path = r'C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\parsed_results.csv'
    
    # ターン分別して出力
    separate_turns_and_export(csv_file_path)