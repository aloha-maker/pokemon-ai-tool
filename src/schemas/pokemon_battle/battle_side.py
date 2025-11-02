from __future__ import annotations
from typing import List, Dict
from .pokemon import Pokemon

# =========================
# --- サイド(味方 or 敵)---
# =========================

class BattleSide:
    """
    自分 or 相手の場を表現
    """
    def __init__(self, team_name: str, pokemon_list: List[Pokemon]):
        self.team_name: str = team_name
        self.team: List[Pokemon] = pokemon_list
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
            "team": [pokemon.to_dict() for pokemon in self.team],
            "active": self.active.to_dict() if self.active else None,
            "screens": self.screens,
            "side_conditions": self.side_conditions,
            "team_size": len(self.team),
            "remaining_members": len([p for p in self.team if p.current_hp > 0])
        }

    def __str__(self) -> str:
        """文字列表現"""
        active_name = self.active.name if self.active else "None"
        return f"BattleSide '{self.team_name}' (Active: {active_name}, Members: {len(self.team)})"

    def __repr__(self) -> str:
        """デバッグ用表現"""
        return f"BattleSide(team_name='{self.team_name}', team_size={len(self.team)}, active='{self.active.name if self.active else None}')"