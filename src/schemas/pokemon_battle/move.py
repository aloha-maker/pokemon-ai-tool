from __future__ import annotations
from typing import Optional, Literal, Dict, List
from .types import TypeName
from src.models.move_model import MoveModel

# =========================
# --- 技 ---
# =========================

class Move:
    def __init__(
        self,
        name: str,
        power: Optional[int | str],
        move_type: TypeName,
        category: Literal["physical", "special", "status"],
        accuracy: float,
        pp: int,
        crit_rate: float = 1/24,
        contact: bool = False,
        effect: Optional[str] = None,
    ):
        self.name: str = name

        # --- 🔧 安全な威力変換 ---
        # None・空文字・不正な文字列に対応して 0 にする
        if power in (None, "", "None"):
            self.power = 0
        else:
            try:
                self.power = int(power)
            except (TypeError, ValueError):
                self.power = 0

        self.type: TypeName = move_type
        self.category: Literal["physical", "special", "status"] = category
        self.accuracy: float = accuracy
        self.pp: int = pp
        self.crit_rate: float = crit_rate
        self.contact: bool = contact
        self.effect: Optional[str] = effect
    
    @classmethod
    def from_model(cls, move_model: MoveModel) -> "Move":
        """
        DBのMoveModelからMoveインスタンスを生成する
        """
        
        # 威力や命中率がnullの場合のデフォルト値設定
        power = move_model.power if move_model.power is not None else 0
        accuracy = move_model.accuracy if move_model.accuracy is not None else 100
        
        # 接触判定（必要に応じて実装）
        contact = False  # ここは技の特性に基づいて設定
        
        return cls(
            name=move_model.name_ja,
            power=power,
            move_type=move_model.type,
            category=move_model.category,
            accuracy=accuracy,
            pp=move_model.pp,
            crit_rate=1/24,  # デフォルト値
            contact=contact,
            effect=None,  # 効果は必要に応じて実装
        )

    @classmethod
    # def from_dict(cls, data: Dict) -> "Move":
    def from_dict(cls, data) -> "Move":
        """
        辞書形式のデータからMoveインスタンスを生成する。
        (to_dictの逆操作)
        """

        move_id = data["name"]
        # move_model = MoveModel.query.filter_by(name_ja=move_name).first()
        move_model = MoveModel.query.filter_by(id=move_id).first()
        move = cls.from_model(move_model=move_model)

        return move

    def to_dict(self) -> Dict:
        """
        Moveインスタンスを辞書形式に変換する
        """
        return {
            "name": self.name,
            "power": self.power,
            "type": self.type,
            "category": self.category,
            "accuracy": self.accuracy,
            "pp": self.pp,
            "crit_rate": self.crit_rate,
            "contact": self.contact,
            "effect": self.effect,
        }
    
    def __repr__(self) -> str:
        return f"Move(name='{self.name}', type='{self.type}', power={self.power}, category='{self.category}')"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.type}) - {self.power}威力 {self.accuracy}%命中"
    
    def get_effective_pp(self, pp_ups: int = 0) -> int:
        """PPアップを考慮した実効PPを計算"""
        if pp_ups < 0:
            pp_ups = 0
        elif pp_ups > 3:
            pp_ups = 3
            
        pp_up_multiplier = 1.0 + (pp_ups * 0.2)
        return int(self.pp * pp_up_multiplier)
    