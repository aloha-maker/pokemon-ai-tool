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

        # 🆕 直近の行動履歴を保持（DamageCalculator連携用）
        self.last_move_user: Optional[str] = None  # 使用者のポケモン名
        self.last_move_name: Optional[str] = None  # 使用技名
        self.last_move_side: Optional[str] = None  # "自分" or "相手"
    
    
    def to_dict(self) -> dict:
        """
        JSONシリアライズ可能な辞書に変換
        
        Returns:
            dict: シリアライズ可能なバトルフィールドデータ
        """
        return {
            'weather': self.weather,
            'terrain': self.terrain,
            'turn': self.turn,
            'is_double': self.is_double,
            'last_move_user': self.last_move_user,
            'last_move_name': self.last_move_name,
            'last_move_side': self.last_move_side
        }