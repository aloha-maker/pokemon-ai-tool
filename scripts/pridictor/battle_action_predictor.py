import pandas as pd
import lightgbm as lgb
import numpy as np
import pickle

# ========== 設定 ==========
MODEL_FILE = r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\battle_action_predictor.txt"
LABEL_ENCODER_FILE = r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\label_encoder.pkl"
FEATURE_CSV = r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\battle_features.csv"

# ========== モデル・エンコーダの読み込み ==========
print("📂 モデルとエンコーダを読み込み中...")

# モデル読み込み
model = lgb.Booster(model_file=MODEL_FILE)

# LabelEncoder読み込み（行動名の変換用）
with open(LABEL_ENCODER_FILE, "rb") as f:
    label_encoder = pickle.load(f)

# 学習時の特徴量を確認するためにCSVを読み込み
df_ref = pd.read_csv(FEATURE_CSV)

# 学習時に使った列名を取得
feature_columns = [col for col in df_ref.columns if col != "my_action"]

print(f"✅ モデルとエンコーダをロードしました。")
print(f"📋 行動ラベル（元のID）: {list(label_encoder.classes_)}")
print(f"📋 特徴量: {feature_columns}")

# ========== ID→名前のマッピング（手動定義が必要） ==========
# CSVが数値IDなので、実際の名前が必要な場合は手動でマッピングを定義
ACTION_NAMES = {
    -1: "（不明/データなし）",
    0: "イナズマドライブ",
    1: "ボルトチェンジ",
    # 他の行動IDも追加
}

POKEMON_NAMES = {
    0: "ミライドン",
    1: "コライドン",
    2: "カイリュー",
    # 他のポケモンIDも追加
}

# ========== 状態入力例（数値IDで指定） ==========
battle_state = {
    "turn": 4,
    "my_pokemon": 0,        # 0 = ミライドン
    "my_hp": 100.0,
    "opp_pokemon": 1,       # 1 = コライドン
    "opp_hp": 46.4,
    "opp_action": 2,        # 2 = インファイト（仮）
    "weather": 0,           # 0 = sunny（仮）
    "boost": -1             # -1 = なし
}

print(f"\n🎮 バトル状態（数値ID）:")
for key, value in battle_state.items():
    print(f"  {key}: {value}")

# ========== 特徴量変換 ==========
# DataFrame化
input_df = pd.DataFrame([battle_state])

# 欠損補完
input_df = input_df.fillna(0)

# 学習時の列順に並べる
for col in feature_columns:
    if col not in input_df.columns:
        input_df[col] = 0

input_df = input_df[feature_columns]

# 全て数値型に変換
input_df = input_df.astype(float)

print(f"\n✅ 特徴量を準備しました: {input_df.shape}")

# ========== 推論 ==========
print("\n🤖 推論中...")
y_pred_proba = model.predict(input_df, num_iteration=model.best_iteration)
y_pred_proba = y_pred_proba[0]

# 予測されたクラスIDを取得
predicted_class_id = y_pred_proba.argmax()
predicted_action_id = label_encoder.inverse_transform([predicted_class_id])[0]
predicted_action_name = ACTION_NAMES.get(predicted_action_id, f"行動ID={predicted_action_id}")

print(f"✅ 最も確率が高い行動: {predicted_action_name} (ID:{predicted_action_id}, {y_pred_proba[predicted_class_id]*100:.1f}%)")

# 上位3つの行動を取得
top_k = min(3, len(label_encoder.classes_))
top_k_idx = np.argsort(y_pred_proba)[::-1][:top_k]

# クラスIDを元の行動IDに変換
top_k_actions = []
for i in top_k_idx:
    action_id = label_encoder.inverse_transform([i])[0]
    action_name = ACTION_NAMES.get(action_id, f"行動ID={action_id}")
    prob = float(y_pred_proba[i])
    top_k_actions.append((action_name, action_id, prob))

# ========== 結果出力 ==========
print(f"\n🎯 推奨行動 TOP{top_k}（確率付き）")
for rank, (action_name, action_id, prob) in enumerate(top_k_actions, start=1):
    print(f"{rank}. {action_name:<30} (ID:{action_id:2d}, {prob*100:.1f}%)")

# 全ての行動の確率を表示
print(f"\n📊 全行動の確率分布:")
all_actions_probs = []
for i in range(len(label_encoder.classes_)):
    action_id = label_encoder.inverse_transform([i])[0]
    action_name = ACTION_NAMES.get(action_id, f"行動ID={action_id}")
    all_actions_probs.append((action_name, action_id, y_pred_proba[i]))

all_actions_probs.sort(key=lambda x: x[2], reverse=True)

for action_name, action_id, prob in all_actions_probs:
    bar = "█" * int(prob * 50)
    print(f"  {action_name:<30} (ID:{action_id:2d}) {prob*100:5.1f}% {bar}")

print(f"\n💡 ヒント: ACTION_NAMESとPOKEMON_NAMESを実際のデータに合わせて編集してください")