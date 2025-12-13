from typing import Dict, Literal

# =========================
# --- 型定義 ---
# =========================

StatName = Literal["hp", "atk", "def", "spa", "spd", "spe"]
NatureModifier = Dict[StatName, float]  # 例: {"atk": 1.1, "spa": 0.9}
TypeName = str  # 例: "みず", "ほのお", "フェアリー"