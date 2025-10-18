import json
import pandas as pd
import re
from pathlib import Path

# ========== 設定 ==========
INPUT_FILE = Path(r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\parsed_results_battle.json")
OUTPUT_FILE = Path(r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\battle_features.csv")

# ========== ユーティリティ関数 ==========
def extract_my_action(actions):
    """自分が使った技・行動を抽出"""
    for act in actions:
        if act["actor"] == "me" and "move" in act:
            return act["move"]
    return None

def extract_opponent_action(actions):
    """相手の代表的な行動（最初に出た技）"""
    for act in actions:
        if act["actor"] == "opponent" and "move" in act:
            # 技名部分を抽出（「バシャーモのブレイズキック」→「ブレイズキック」）
            move = re.sub(r".*の", "", act["move"])
            return move.strip()
    return None

def extract_field_info(actions):
    """天候やフィールド、能力上昇などを一部検出（任意拡張可）"""
    field = {"weather": None, "boost": None}
    for act in actions:
        text = act.get("move") or act.get("ability") or ""
        if "日差し" in text:
            field["weather"] = "sunny"
        if "素早さが上がった" in text:
            field["boost"] = "speed_up"
        if "攻撃がぐーんと上がった" in text:
            field["boost"] = "atk_up"
    return field

# ========== メイン処理 ==========
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        battle_log = json.load(f)

    records = []
    for entry in battle_log:
        turn = entry["turn"]
        my_poke = entry.get("my_pokemon")
        opp_poke = entry.get("opp_pokemon")
        my_hp = entry.get("my_hp", None)
        opp_hp = entry.get("opp_hp", None)

        actions = entry.get("actions", [])
        my_action = extract_my_action(actions)
        opp_action = extract_opponent_action(actions)
        field = extract_field_info(actions)

        record = {
            "turn": turn,
            "my_pokemon": my_poke,
            "opp_pokemon": opp_poke,
            "my_hp": my_hp,
            "opp_hp": opp_hp,
            "my_action": my_action,
            "opp_action": opp_action,
            "weather": field["weather"],
            "boost": field["boost"],
        }
        records.append(record)

    df = pd.DataFrame(records)

    # 特徴エンコード例（カテゴリ→整数IDなど）
    for col in ["my_pokemon", "opp_pokemon", "my_action", "opp_action", "weather", "boost"]:
        df[col] = df[col].astype("category").cat.codes

    print(df.head())
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ 特徴量CSVを出力しました → {OUTPUT_FILE.absolute()}")

if __name__ == "__main__":
    main()
