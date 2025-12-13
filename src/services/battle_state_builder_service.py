from __future__ import annotations
from typing import Optional, List

from src.models.trained_pokemon_moedl import TrainedPokemonModel
from src.models.pokemon_model import PokemonModel

from src.schemas.pokemon_battle.battle_log import BattleLog
from src.schemas.pokemon_battle.battle_state import BattleState
from src.schemas.pokemon_battle.battle_side import BattleSide
from src.schemas.pokemon_battle.battle_field import BattleField
from src.schemas.pokemon_battle.pokemon import Pokemon


class BattleStateBuilder:
    """
    BattleLog（スキーマ層）からBattleState（状態層）を構築するビルダー。
    - 自分側: TrainedPokemonModelから生成
    - 相手側: PokemonModelから簡易生成
    """

    @staticmethod
    def from_battle_log(battle_log: BattleLog) -> BattleState:
        """
        BattleLogからBattleStateを生成。
        """

        # ------------------------
        # 1️⃣ 自分側・相手側パーティ構築
        # ------------------------
        my_team: List[Pokemon] = []
        opponent_team: List[Pokemon] = []

        for party_log in battle_log.parties:
            pokemon_name = party_log.pokemon_name

            # 自分側
            if not party_log.is_opponent:
                trained_model: Optional[TrainedPokemonModel] = None
                if party_log.pokemon_id:
                    trained_model = TrainedPokemonModel.query.get(party_log.pokemon_id)

                if trained_model:
                    pokemon = Pokemon.from_trained_model(trained_model)
                else:
                    # Trainedデータが無い場合はfallbackでbaseモデルを利用
                    base_model = PokemonModel.query.filter_by(name_ja=pokemon_name).first()
                    if base_model:
                        pokemon = Pokemon.from_pokemon_model(base_model, level=50)
                    else:
                        raise ValueError(f"Pokemon '{pokemon_name}' not found in DB")

                my_team.append(pokemon)

            # 相手側
            else:
                base_model = PokemonModel.query.filter_by(name_ja=pokemon_name).first()
                if base_model:
                    pokemon = Pokemon.from_pokemon_model(base_model, level=50)
                    opponent_team.append(pokemon)
                else:
                    raise ValueError(f"Opponent Pokemon '{pokemon_name}' not found in DB")

        # if not my_team or not opponent_team:
        #     raise ValueError("BattleLogに十分なパーティ情報がありません。")

        # ------------------------
        # 2️⃣ サイド構築
        # ------------------------
        my_side = BattleSide(team_name="自分", pokemon_list=my_team)
        opponent_side = BattleSide(team_name="相手", pokemon_list=opponent_team)

        # ------------------------
        # 3️⃣ フィールド構築
        # ------------------------
        field = BattleField(
            weather=None,
            terrain=None,
            turn=0,
            is_double=(battle_log.battle_format == "ダブル"),
        )

        # ------------------------
        # 4️⃣ BattleState生成
        # ------------------------
        battle_state = BattleState(
            side1=my_side,
            side2=opponent_side,
            field=field,
            is_side1_attacker=True,
        )

        return battle_state