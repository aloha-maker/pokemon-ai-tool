from __future__ import annotations
from typing import Optional, List, Dict
from .types import StatName, TypeName
from .move import Move
from src.models.pokemon_model import PokemonModel
from src.models.trained_pokemon_moedl import TrainedPokemonModel


# =========================
# --- ポケモン ---
# =========================

class Pokemon:
    def __init__(
        self,
        name: str,
        level: int,
        base_stats: Dict[StatName, int],
        iv: Dict[StatName, int],
        ev: Dict[StatName, int],
        nature: str,
        ability: str,
        item: Optional[str],
        types: List[TypeName],
        tera_type: Optional[TypeName] = None,
        status: Optional[str] = None,
        current_hp: Optional[int] = None,
    ):
        self.name: str = name
        self.level: int = level
        self.base_stats: Dict[StatName, int] = base_stats
        self.iv: Dict[StatName, int] = iv
        self.ev: Dict[StatName, int] = ev
        self.nature: str = nature
        self.ability: str = ability
        self.item: Optional[str] = item
        self.types: List[TypeName] = types
        self.tera_type: Optional[TypeName] = tera_type
        self.status: Optional[str] = status

        # ステータス補正段階(-6~+6)
        self.boosts: Dict[StatName, int] = {
            "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0
        }

        # 最大・現在HPを管理
        self.max_hp: int = self.calculate_hp()
        self.current_hp: int = current_hp if current_hp is not None else self.max_hp

        # 技リスト
        self.moves: List[Move] = []

    def calculate_hp(self) -> int:
        """HPの実数値を計算"""
        base = self.base_stats["hp"]
        iv = self.iv["hp"]
        ev = self.ev["hp"]
        return ((base * 2 + iv + (ev // 4)) * self.level // 100) + self.level + 10

    def calculate_stat(self, stat: StatName) -> int:
        """HP以外の実数値を計算(性格補正を後で反映)"""
        base = self.base_stats[stat]
        iv = self.iv[stat]
        ev = self.ev[stat]
        stat_value = ((base * 2 + iv + (ev // 4)) * self.level // 100) + 5
        # 性格補正を反映(ここでは仮に1.0固定。後でNatureデータで調整可能)
        return int(stat_value * 1.0)
    
    @classmethod
    def from_trained_model(cls, trained: TrainedPokemonModel) -> "Pokemon":
        """
        DBのTrainedPokemonModelからPokemonインスタンスを生成する。
        """
        # --- 種族データを参照 ---
        base_model = PokemonModel.query.get(trained.pokemon_id)
        if base_model is None:
            raise ValueError(f"Base Pokemon not found for id={trained.pokemon_id}")

        # --- ステータス辞書を構築 ---
        base_stats = {
            "hp": base_model.hp,
            "atk": base_model.attack,
            "def": base_model.defense,
            "spa": base_model.sp_attack,
            "spd": base_model.sp_defense,
            "spe": base_model.speed,
        }

        iv = {
            "hp": trained.iv_hp, "atk": trained.iv_atk, "def": trained.iv_def,
            "spa": trained.iv_spa, "spd": trained.iv_spd, "spe": trained.iv_spe
        }

        ev = {
            "hp": trained.ev_hp, "atk": trained.ev_atk, "def": trained.ev_def,
            "spa": trained.ev_spa, "spd": trained.ev_spd, "spe": trained.ev_spe
        }

        # --- タイプを構築 ---
        types = [base_model.type1]
        if base_model.type2:
            types.append(base_model.type2)

        # --- インスタンス生成 ---
        pokemon = cls(
            name=trained.nickname or base_model.name,
            level=trained.level,
            base_stats=base_stats,
            iv=iv,
            ev=ev,
            nature="まじめ",      # 後でNatureテーブルと連携
            ability=str(trained.ability_id),  # 後でAbilitiesとJOIN
            item=str(trained.held_item_id),   # 後でItemsとJOIN
            types=types,
        )

        return pokemon
    
    def to_dict(self) -> Dict:
        """
        Pokemonインスタンスを辞書形式に変換する
        """
        return {
            "name": self.name,
            "level": self.level,
            "base_stats": self.base_stats,
            "iv": self.iv,
            "ev": self.ev,
            "nature": self.nature,
            "ability": self.ability,
            "item": self.item,
            "types": self.types,
            "tera_type": self.tera_type,
            "status": self.status,
            "boosts": self.boosts,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "moves": [move.to_dict() for move in self.moves] if self.moves else [],
            "calculated_stats": {
                "hp": self.calculate_hp(),
                "atk": self.calculate_stat("atk"),
                "def": self.calculate_stat("def"),
                "spa": self.calculate_stat("spa"),
                "spd": self.calculate_stat("spd"),
                "spe": self.calculate_stat("spe"),
            }
        }