import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, top_k_accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

# ========== 設定 ==========
INPUT_FILE = r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\battle_features.csv"
TARGET_COL = "my_action"
TEST_SIZE = 0.2
RANDOM_SEED = 42
MIN_SAMPLES_TOTAL = 5  # 最低限必要なデータ数

# ========== データ読み込み ==========
print("📂 CSV読み込み中...")
df = pd.read_csv(INPUT_FILE)

if TARGET_COL not in df.columns:
    raise ValueError(f"❌ {TARGET_COL} 列がCSVに存在しません。")

# 欠損補完
df = df.fillna(0)

# 目的変数と特徴量分離
X = df.drop(columns=[TARGET_COL])
y = df[TARGET_COL]

# ========== クラス分布確認 ==========
print("\n📊 元のクラス分布:")
print(y.value_counts())
print(f"ユニークな値: {sorted(y.unique())}")

# ========== ラベルエンコーディング ==========
print("\n🔄 ラベルを 0, 1, 2, ... に変換中...")
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

print(f"✅ 変換後のクラス数: {len(label_encoder.classes_)}")
print(f"クラスマッピング:")
for original, encoded in zip(label_encoder.classes_, range(len(label_encoder.classes_))):
    print(f"  {original} -> {encoded}")

# ========== クラス分布確認（エンコード後） ==========
class_counts = pd.Series(y_encoded).value_counts()
print("\n📊 エンコード後のクラス分布:")
print(class_counts)

# サンプル数が1つだけのクラスのみ除外（最低限の処理）
valid_classes = class_counts[class_counts >= 2].index
invalid_classes = class_counts[class_counts < 2].index

if len(invalid_classes) > 0:
    print(f"\n⚠️ サンプルが1つしかないクラスを除外します: {list(invalid_classes)}")
    original_labels = label_encoder.inverse_transform(invalid_classes)
    print(f"   元のラベル: {list(original_labels)}")
    mask = pd.Series(y_encoded).isin(valid_classes)
    X = X[mask]
    y_encoded = y_encoded[mask]
    
    # 再度クラス分布を確認
    class_counts_after = pd.Series(y_encoded).value_counts()
    print(f"\n📊 除外後のクラス分布:")
    print(class_counts_after)

# データが最低限残っているか確認
if len(y_encoded) < MIN_SAMPLES_TOTAL:
    raise ValueError(f"❌ データが少なすぎます（{len(y_encoded)}件）。最低{MIN_SAMPLES_TOTAL}件必要です。")

# ========== データ分割 ==========
# データ数とクラス数に応じて分割方法を調整
n_samples = len(y_encoded)
n_classes = len(pd.Series(y_encoded).unique())

# テストサイズを調整（データが少ない場合は1サンプルのみテスト）
if n_samples < 10:
    actual_test_size = 1  # 絶対数で指定
    print(f"\n⚠️ データが少ないため、テストサイズを1サンプルに調整します")
else:
    actual_test_size = TEST_SIZE

# stratifyを使うか判断（クラス数が多すぎる場合は使わない）
use_stratify = (n_classes >= 2 and n_samples >= n_classes * 2 and 
                (isinstance(actual_test_size, float) and n_samples * actual_test_size >= n_classes) or
                (isinstance(actual_test_size, int) and actual_test_size >= n_classes))

try:
    if use_stratify:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=actual_test_size, random_state=RANDOM_SEED, stratify=y_encoded
        )
        print(f"\n✅ データ分割完了（stratify使用）: train={len(X_train)} test={len(X_test)}")
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=actual_test_size, random_state=RANDOM_SEED
        )
        print(f"\n✅ データ分割完了（stratifyなし）: train={len(X_train)} test={len(X_test)}")
except ValueError as e:
    # それでもエラーが出る場合は、最もシンプルな分割に切り替え
    print(f"\n⚠️ stratify分割に失敗: {e}")
    print("   最もシンプルな分割を試みます...")
    if n_samples >= 2:
        test_size_simple = 1
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size_simple, random_state=RANDOM_SEED
        )
        print(f"✅ データ分割完了（単純分割）: train={len(X_train)} test={len(X_test)}")
    else:
        raise ValueError("❌ データが少なすぎて分割できません（最低2サンプル必要）")

# ========== LightGBMデータセット ==========
train_data = lgb.Dataset(X_train, label=y_train)
test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

# ========== ハイパーパラメータ ==========
params = {
    "objective": "multiclass",
    "num_class": len(pd.Series(y_encoded).unique()),
    "metric": "multi_logloss",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "verbosity": -1,
    "seed": RANDOM_SEED
}

# ========== モデル学習 ==========
print("\n🚀 モデル学習を開始します...")

callbacks = [
    lgb.early_stopping(stopping_rounds=30, verbose=True),
    lgb.log_evaluation(period=50)
]

model = lgb.train(
    params=params,
    train_set=train_data,
    valid_sets=[train_data, test_data],
    valid_names=["train", "valid"],
    num_boost_round=500,
    callbacks=callbacks
)

# ========== 評価 ==========
print("\n🔍 評価中...")
y_pred_proba = model.predict(X_test, num_iteration=model.best_iteration)
y_pred = y_pred_proba.argmax(axis=1)

acc = accuracy_score(y_test, y_pred)

# Top-k精度はクラス数が十分にある場合のみ計算
if len(pd.Series(y_encoded).unique()) >= 3:
    top3 = top_k_accuracy_score(y_test, y_pred_proba, k=min(3, len(pd.Series(y_encoded).unique())))
    print(f"\n✅ Accuracy: {acc:.4f}")
    print(f"✅ Top-3 Accuracy: {top3:.4f}")
else:
    print(f"\n✅ Accuracy: {acc:.4f}")
    print(f"   (クラス数が少ないためTop-3精度はスキップ)")

# 元のラベルに戻して表示
y_test_original = label_encoder.inverse_transform(y_test)
y_pred_original = label_encoder.inverse_transform(y_pred)

print("\n=== Classification Report (元のラベル) ===")
print(classification_report(y_test_original, y_pred_original, zero_division=0))

# ========== 可視化 ==========
# Confusion Matrix
plt.figure(figsize=(10,8))
cm = confusion_matrix(y_test_original, y_pred_original)
# ラベルが多い場合は回転
labels = label_encoder.classes_
rotation = 45 if len(labels) > 10 else 0
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
            xticklabels=labels, 
            yticklabels=labels)
plt.title("Confusion Matrix (Predicted vs Actual)")
plt.xlabel("Predicted")
plt.ylabel("Actual")
if rotation > 0:
    plt.xticks(rotation=rotation, ha='right')
    plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

# 特徴重要度（特徴量が十分にある場合のみ）
try:
    if len(X.columns) > 0:
        max_features = min(15, len(X.columns))
        # 重要度を取得してチェック
        importance = model.feature_importance(importance_type='gain')
        if importance.sum() > 0:  # 重要度が計算されているか確認
            lgb.plot_importance(model, max_num_features=max_features, importance_type="gain", figsize=(8,6))
            plt.title("Feature Importance (gain)")
            plt.tight_layout()
            plt.show()
        else:
            print("\n⚠️ 特徴量の重要度が計算されていないため、プロットをスキップします")
    else:
        print("\n⚠️ 特徴量が少ないため、重要度プロットをスキップします")
except Exception as e:
    print(f"\n⚠️ 特徴重要度のプロット中にエラーが発生しました: {e}")
    print("   プロットをスキップして続行します")

# ========== モデル保存 ==========
model.save_model(r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\battle_action_predictor.txt")
print("\n💾 モデルを保存しました: battle_action_predictor.txt")

# LabelEncoderも保存（推論時に必要）
with open(r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\label_encoder.pkl", "wb") as f:
    pickle.dump(label_encoder, f)
print("💾 LabelEncoderを保存しました: label_encoder.pkl")

print("\n🎉 学習完了！推論スクリプトで行動予測が可能です。")
print("\n📌 推論時の注意:")
print("  1. モデル読み込み: lgb.Booster(model_file='...')")
print("  2. LabelEncoder読み込み: pickle.load(open('label_encoder.pkl', 'rb'))")
print("  3. 予測結果を元のラベルに変換: label_encoder.inverse_transform(pred)")