from __future__ import annotations
from typing import Any, Dict
from .battle_side import BattleSide
from .battle_field import BattleField

# =========================
# --- 戦闘全体 ---
# =========================

class BattleState:
    """
    バトル全体の状態(両サイド+環境)
    """
    def __init__(
        self,
        side1: BattleSide,
        side2: BattleSide,
        field: BattleField,
        is_side1_attacker: bool = True  # どちらが攻撃側か
    ):
        self.side1: BattleSide = side1  # 自分側
        self.side2: BattleSide = side2  # 相手側
        self.field: BattleField = field
        self.is_side1_attacker: bool = is_side1_attacker

    def get_attacker_side(self) -> BattleSide:
        """攻撃側のサイドを返す"""
        return self.side1 if self.is_side1_attacker else self.side2

    def get_defender_side(self) -> BattleSide:
        """防御側のサイドを返す"""
        return self.side2 if self.is_side1_attacker else self.side1

    def get_opponent(self, side: BattleSide) -> BattleSide:
        """与えられたサイドの反対側を返す"""
        return self.side2 if side is self.side1 else self.side1

    def switch_attacker(self) -> None:
        """攻撃側を切り替える"""
        self.is_side1_attacker = not self.is_side1_attacker

    def set_attacker(self, side: BattleSide) -> None:
        """特定のサイドを攻撃側に設定"""
        self.is_side1_attacker = (side is self.side1)

    def update_sides(self, attacker_side: BattleSide, defender_side: BattleSide):
        """攻撃側・防御側を新しい状態に更新"""
        self.attacker_side = attacker_side
        self.defender_side = defender_side

    def to_dict(self) -> Dict[str, Any]:
        """
        JSONシリアライズ可能な辞書に変換
        
        Returns:
            Dict[str, Any]: シリアライズ可能なバトル状態データ
        """
        return {
            'side1': self.side1.to_dict(),
            'side2': self.side2.to_dict(),
            'field': self.field.to_dict(),
            'is_side1_attacker': self.is_side1_attacker
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BattleState:
        """
        辞書データから BattleState インスタンスを復元する

        Args:
            data (Dict[str, Any]): BattleState の辞書データ

        Returns:
            BattleState: 復元されたバトル状態
        """
        side1 = BattleSide.from_dict(data['side1'])
        side2 = BattleSide.from_dict(data['side2'])
        field = BattleField.from_dict(data['field'])
        is_side1_attacker = data.get('is_side1_attacker', True)

        return cls(
            side1=side1,
            side2=side2,
            field=field,
            is_side1_attacker=is_side1_attacker
        )