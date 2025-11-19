from __future__ import annotations
from functools import partial
from typing import Optional, List, Dict
from .types import StatName, TypeName
from .move import Move
from src.models.pokemon_model import PokemonModel
from src.models.trained_pokemon_moedl import TrainedPokemonModel
from src.models.move_model import MoveModel


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
        self.status: Optional[str] = status # 状態異常

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
    
    def _load_moves_from_trained_model(self, trained: TrainedPokemonModel) -> List[Move]:
        """TrainedPokemonModelから技を読み込む"""
        moves = []
        move_ids = [
            trained.move1_id, 
            trained.move2_id, 
            trained.move3_id, 
            trained.move4_id
        ]
        
        for move_id in move_ids:
            if move_id is not None:
                move_model = MoveModel.query.get(move_id)
                if move_model:
                    move = Move.from_model(move_model)
                    moves.append(move)
        
        return moves
    
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
            name=base_model.name_ja,
            level=trained.level,
            base_stats=base_stats,
            iv=iv,
            ev=ev,
            status=None,
            nature=str(trained.nature_id),
            ability=str(trained.ability_id),
            item=str(trained.held_item_id),
            tera_type= str(trained.tera_type_id),
            types=types,
        )

        # --- 技を設定 ---
        pokemon.moves = pokemon._load_moves_from_trained_model(trained)

        return pokemon

    # === PokemonModel用 ===
    @classmethod
    def from_pokemon_model(cls, base_model: PokemonModel, level: int = 50) -> "Pokemon":
        """
        Trainedデータがないときに、PokemonModel単体から生成する簡易版。
        - IV: 全て31
        - EV: 全て0
        - Nature: まじめ
        - Ability/Item: なし
        """

        base_stats = {
            "hp": base_model.hp,
            "atk": base_model.attack,
            "def": base_model.defense,
            "spa": base_model.sp_attack,
            "spd": base_model.sp_defense,
            "spe": base_model.speed,
        }

        iv = {stat: 31 for stat in ["hp", "atk", "def", "spa", "spd", "spe"]}
        ev = {stat: 0 for stat in ["hp", "atk", "def", "spa", "spd", "spe"]}

        types = [base_model.type1]
        if base_model.type2:
            types.append(base_model.type2)

        pokemon = cls(
            name=base_model.name_ja,
            level=level,
            base_stats=base_stats,
            iv=iv,
            ev=ev,
            
            nature=None,
            ability=None,
            item=None,
            types=types,
        )

        return pokemon
    
    def add_move(self, move: Move) -> None:
        """技を追加する"""
        if len(self.moves) < 4:
            self.moves.append(move)
        else:
            raise ValueError("ポケモンは最大4つまで技を覚えられます")
    
    def remove_move(self, move_index: int) -> None:
        """指定したインデックスの技を削除する"""
        if 0 <= move_index < len(self.moves):
            self.moves.pop(move_index)
    
    def get_move(self, move_name: str) -> Optional[Move]:
        """技名から技を取得する"""
        for move in self.moves:
            if move.name == move_name:
                return move
        return None

    @classmethod
    def from_dict(cls, data: Dict) -> "Pokemon":
        """
        辞書形式のデータからPokemonインスタンスを生成する。
        (to_dictの逆操作)
        """
        # まずPokemonModelからname_jaを検索
        pokemon_name = data["name"]
        base_model = PokemonModel.query.filter_by(name_ja=pokemon_name).first()
        
        # 種族データから基本インスタンスを生成
        pokemon = cls.from_pokemon_model(base_model=base_model, level=data.get("level", 50))
        
        # 個体値・努力値・性格など個別データで上書き
        pokemon.iv = data.get("iv", {stat: 31 for stat in ["hp", "atk", "def", "spa", "spd", "spe"]})
        pokemon.ev = data["ev"]
        pokemon.nature = data["nature"]
        pokemon.ability = data["ability"]
        pokemon.item = data["item"]
        pokemon.tera_type = data.get("tera_type")
        pokemon.status = data.get("status")
        pokemon.current_hp = data.get("current_hp")

        # 2. __init__以外で設定される属性を辞書から復元
        
        # 能力ランク (デフォルトは0だが、保存された状態を復元)
        if "boosts" in data:
            pokemon.boosts = data["boosts"]

        # 技リスト (Move.from_dict が存在することを前提とする)
        if "moves" in data and data["moves"]:
            pokemon.moves = [Move.from_dict(move_data) for move_data in data["moves"]]
        
        # calculated_stats は動的に計算されるため、復元不要

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