import pandas as pd
import os
import json
import re

def parse_battle_log_to_json(text_file_path):
    """
    バトルログのテキストファイルをJSON形式に変換
    """
    with open(text_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    turns = []
    current_turn = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # ターン開始を検出
        turn_match = re.search(r'(\d+)：\s*(\d+)ターン目：', line)
        if turn_match:
            if current_turn is not None:
                turns.append(current_turn)
            
            frame = int(turn_match.group(1))
            turn_num = int(turn_match.group(2))
            
            current_turn = {
                "turn": turn_num,
                "my_pokemon": "",
                "my_hp": 100,
                "opp_pokemon": "",
                "opp_hp": 100,
                "actions": []
            }
            continue
        
        # 0ターン目をスキップ
        if line == "0ターン目：" or "0ターン目：" in line:
            continue
        
        # バトル基本情報をスキップ
        if "BATTLE-" in line and "：" in line and "ターン目" not in line:
            continue
        
        # 自分のポケモン情報を解析
        my_pokemon_match = re.search(r'(\d+)：\s*自分：([^ ]+) HP(\d+(?:\.\d+)?)％\s*(.*)', line)
        if my_pokemon_match and current_turn is not None:
            frame = int(my_pokemon_match.group(1))
            pokemon_name = my_pokemon_match.group(2)
            hp = float(my_pokemon_match.group(3))
            ailment = my_pokemon_match.group(4).strip()
            
            current_turn["my_pokemon"] = pokemon_name
            current_turn["my_hp"] = hp
            continue
        
        # 相手のポケモン情報を解析
        opp_pokemon_match = re.search(r'(\d+)：\s*相手：([^ ]+) HP(\d+(?:\.\d+)?)％\s*(.*)', line)
        if opp_pokemon_match and current_turn is not None:
            frame = int(opp_pokemon_match.group(1))
            pokemon_name = opp_pokemon_match.group(2)
            hp = float(opp_pokemon_match.group(3))
            ailment = opp_pokemon_match.group(4).strip()
            
            current_turn["opp_pokemon"] = pokemon_name
            current_turn["opp_hp"] = hp
            continue
        
        # アクションを解析（特性・コメント行）
        action_match = re.search(r'(\d+)：\s*　　(.*)', line)
        if action_match and current_turn is not None:
            frame = int(action_match.group(1))
            action_text = action_match.group(2)
            
            # アクションの種類を判定
            action = parse_action(action_text, current_turn)
            if action:
                current_turn["actions"].append(action)
    
    # 最後のターンを追加
    if current_turn is not None:
        turns.append(current_turn)
    
    return turns

def parse_action(action_text, current_turn):
    """
    アクションテキストを解析してJSON形式に変換
    """
    # 技を使用した場合
    move_patterns = [
        (r'([^は]+)は(.+?)をつかった！', 'opponent'),
        (r'([^の]+)の(.+?)！', 'both'),
        (r'(.+?)を使った！', 'me'),
        (r'(.+?)をつかった！', 'me')
    ]
    
    for pattern, default_actor in move_patterns:
        match = re.search(pattern, action_text)
        if match:
            if default_actor == 'both':
                # ポケモン名から行動者を判定
                pokemon_name = match.group(1)
                move_name = match.group(2)
                
                if pokemon_name == current_turn["my_pokemon"]:
                    actor = "me"
                elif pokemon_name == current_turn["opp_pokemon"]:
                    actor = "opponent"
                else:
                    actor = "opponent"  # デフォルト
                
                return {"actor": actor, "move": move_name}
            else:
                move_name = match.group(1) if default_actor == 'me' else match.group(2)
                return {"actor": default_actor, "move": move_name}
    
    # 特性の発動
    ability_patterns = [
        (r'([^の]+)の([^の]+)', 'both'),
        (r'(.+)', 'opponent')  # デフォルトで相手の特性
    ]
    
    for pattern, default_actor in ability_patterns:
        match = re.search(pattern, action_text)
        if match:
            if default_actor == 'both':
                pokemon_name = match.group(1)
                ability_name = match.group(2)
                
                if pokemon_name == current_turn["my_pokemon"]:
                    actor = "me"
                elif pokemon_name == current_turn["opp_pokemon"]:
                    actor = "opponent"
                else:
                    actor = "opponent"
                
                return {"actor": actor, "ability": ability_name}
            else:
                ability_name = match.group(1)
                return {"actor": default_actor, "ability": ability_name}
    
    # 状態変化やその他のアクション
    other_patterns = [
        (r'効果はバツグンだ！', None, "super_effective"),
        (r'効果は今ひとつのようだ……', None, "not_very_effective"),
        (r'(.+?)はたおれた！', 'both', "fainted"),
        (r'(.+?)に交代！', 'me', "switch"),
        (r'(.+?)をくりだした！', 'opponent', "send_out"),
        (r'(.+?)があらわれた！', 'opponent', "send_out")
    ]
    
    for pattern, default_actor, action_type in other_patterns:
        match = re.search(pattern, action_text)
        if match:
            if default_actor == 'both':
                pokemon_name = match.group(1)
                if pokemon_name == current_turn["my_pokemon"]:
                    actor = "me"
                else:
                    actor = "opponent"
            else:
                actor = default_actor
            
            return {"actor": actor, "action": action_type, "target": match.group(1) if match.groups() else None}
    
    return None

def save_json_output(turns_data, output_file_path):
    """
    JSONデータをファイルに保存
    """
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(turns_data, f, ensure_ascii=False, indent=2)

def process_battle_data(csv_file_path):
    """
    CSVからJSONへの一連の処理を実行
    """
    # 入力ファイルのパスから出力ファイル名を生成
    input_dir = os.path.dirname(csv_file_path)
    input_filename = os.path.splitext(os.path.basename(csv_file_path))[0]
    
    # テキストファイルのパス
    text_file_path = os.path.join(input_dir, f"{input_filename}_output.txt")
    json_file_path = os.path.join(input_dir, f"{input_filename}_battle.json")
    
    # テキストファイルが存在するか確認
    if not os.path.exists(text_file_path):
        print(f"テキストファイルが見つかりません: {text_file_path}")
        return
    
    # テキストファイルをJSONに変換
    turns_data = parse_battle_log_to_json(text_file_path)
    
    # JSONを保存
    save_json_output(turns_data, json_file_path)
    
    print(f"JSON変換完了: {json_file_path}")
    print(f"合計 {len(turns_data)} ターンのデータを変換しました")
    
    # 結果を表示
    for turn in turns_data:
        print(f"\nターン {turn['turn']}:")
        print(f"  自分: {turn['my_pokemon']} HP{turn['my_hp']}%")
        print(f"  相手: {turn['opp_pokemon']} HP{turn['opp_hp']}%")
        print(f"  アクション: {len(turn['actions'])}件")

# 使用例
if __name__ == "__main__":
    # 処理したいCSVファイルのパスを指定
    csv_file_path = r'C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\parsed_results.csv'
    
    # バトルデータを処理
    process_battle_data(csv_file_path)