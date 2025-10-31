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
        self.active: Pokemon = pokemon_list[0]  # 現在場に出ているポケモン

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