from typing import Optional

# =========================
# --- 戦闘フィールド(共通環境)---
# =========================

class BattleField:
    def __init__(
        self,
        weather: Optional[str] = None,
        terrain: Optional[str] = None,
        turn: int = 0,
        is_double: bool = False,
    ):
        self.weather: Optional[str] = weather      # 例: "sunny", "rain"
        self.terrain: Optional[str] = terrain      # 例: "electric", "grassy"
        self.turn: int = turn
        self.is_double: bool = is_double