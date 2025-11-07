from __future__ import annotations
from typing import List, Dict
from .party import Party
from .pokemon import Pokemon

# =========================
# --- サイド(味方 or 敵)---
# =========================

class BattleSide:
    """
    自分 or 相手の場を表現
    """
    def __init__(self, team_name: str, party: Party):
        self.team_name = team_name
        self.team: Party = party
        self.active: Pokemon =  None  # 現在場に出ているポケモン

        # サイド特有の効果(壁、ステルスロックなど)
        self.screens: Dict[str, bool] = {
            "reflect": False,
            "light_screen": False,
            "aurora_veil": False,
        }
        self.side_conditions: Dict[str, int | bool] = {
            "spikes": 0,
            "toxic_spikes": 0,
            "stealth_rock": False,
            "tailwind": False,
        }

    def set_active(self, pokemon: Pokemon) -> None:
        """場に出すポケモンを変更"""
        self.active = pokemon

    def to_dict(self) -> Dict:
        """
        BattleSideインスタンスを辞書形式に変換する
        """
        return {
            "team_name": self.team_name,
            "team": self.team.to_dict(),
            "active": self.active.to_dict() if self.active else None,
            "screens": self.screens,
            "side_conditions": self.side_conditions,
            "team_size": len(self.team),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> BattleSide:
        """
        辞書データから BattleSide インスタンスを復元する

        Args:
            data (Dict): BattleSide の辞書データ

        Returns:
            BattleSide: 復元された BattleSide インスタンス
        """
        # Partyを復元
        team = Party.from_dict(data["team"])
        # インスタンス生成
        instance = cls(team_name=data["team_name"], party=team)

        # activeポケモンが存在する場合のみ復元
        if data.get("active"):
            instance.active = Pokemon.from_dict(data["active"])

        # 壁・設置技状態などを復元
        instance.screens = data.get("screens", {
            "reflect": False,
            "light_screen": False,
            "aurora_veil": False,
        })
        instance.side_conditions = data.get("side_conditions", {
            "spikes": 0,
            "toxic_spikes": 0,
            "stealth_rock": False,
            "tailwind": False,
        })

        return instance

    def __str__(self) -> str:
        """文字列表現"""
        active_name = self.active.name if self.active else "None"
        return f"BattleSide '{self.team_name}' (Active: {active_name}, Members: {len(self.team)})"

    def __repr__(self) -> str:
        """デバッグ用表現"""
        return f"BattleSide(team_name='{self.team_name}', team_size={len(self.team)}, active='{self.active.name if self.active else None}')"