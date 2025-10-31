"""
修正版 calculate.py - ダメージ計算（クラス版）
"""
import random
import json
from pathlib import Path
from typing import Tuple

# 分割したモジュールから必要なクラスをインポート
from src.schemas.pokemon_battle import Pokemon, Move, BattleSide, BattleField, BattleState
from config import Config


class DamageCalculator:
    """ダメージ計算クラス"""
    
    def __init__(self):
        """
        Args:
            type_chart_path: タイプ相性表のJSONファイルパス（デフォルトはconfig設定）
        """
        self.TYPE_CHART = self._load_type_chart()
    
    def _load_type_chart(self) -> dict[str, dict[str, float]]:
        """タイプ相性表をJSONファイルから読み込む"""
        try:
            with open(Path(Config.TYPE_CHART_PATH), 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"タイプ相性表ファイルが見つかりません: {self.type_chart_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"タイプ相性表のJSON形式が不正です: {e}")

    def get_screen_modifier(self, move: Move, defender_side: BattleSide) -> float:
        """壁(リフレクター・ひかりのかべ)による補正"""
        if move.category == "physical" and defender_side.screens["reflect"]:
            return 0.5
        if move.category == "special" and defender_side.screens["light_screen"]:
            return 0.5
        return 1.0

    def get_weather_modifier(self, move: Move, field: BattleField) -> float:
        """天候による補正"""
        if field.weather == "rain":
            if move.type == "みず":
                return 1.5
            elif move.type == "ほのお":
                return 0.5
        elif field.weather == "sunny":
            if move.type == "ほのお":
                return 1.5
            elif move.type == "みず":
                return 0.5
        return 1.0

    def get_type_effectiveness(self, move: Move, defender: Pokemon) -> float:
        """
        攻撃側の技タイプと防御側の複合タイプから
        実際のダメージ倍率(0〜4倍)を算出する。
        """
        result = 1.0
        atk_type = move.type

        for def_type in defender.types:
            # タイプ表に存在しない場合は等倍扱い
            if atk_type not in self.TYPE_CHART:
                multiplier = 1.0
            else:
                multiplier = self.TYPE_CHART[atk_type].get(def_type, 1.0)

            result *= multiplier

        return result

    def get_stab(self, attacker: Pokemon, move: Move) -> float:
        """タイプ一致ボーナス(STAB)の計算"""
        # テラスタルを優先(同タイプなら2倍、非一致なら1.5倍)
        if attacker.tera_type == move.type:
            return 2.0
        elif move.type in attacker.types:
            return 1.5
        else:
            return 1.0

    def get_random_modifier(self) -> float:
        """乱数補正(0.85〜1.00)"""
        return random.uniform(0.85, 1.00)

    def calculate_damage(
        self,
        move: Move,
        battle_state: BattleState,
    ) -> Tuple[int, int]:
        """
        ダメージの最小値・最大値を計算して返す。
        
        Args:
            attacker: 攻撃側のポケモン
            defender: 防御側のポケモン
            move: 使用する技
            battlefield: バトルフィールドの状態
            attacker_side: 攻撃側のサイド
            defender_side: 防御側のサイド
        
        Returns:
            (最小ダメージ, 最大ダメージ)のタプル
        """

        # BattleStateから必要な情報を取得
        attacker_side = battle_state.get_attacker_side()
        defender_side = battle_state.get_defender_side()
        attacker = attacker_side.active
        defender = defender_side.active
        battlefield = battle_state.field

        # 1️⃣ 攻撃・防御ステータス算出
        if move.category == "physical":
            A = attacker.calculate_stat("atk")
            D = defender.calculate_stat("def")
        elif move.category == "special":
            A = attacker.calculate_stat("spa")
            D = defender.calculate_stat("spd")
        else:
            return (0, 0)  # 変化技の場合はダメージなし

        # 2️⃣ 基本ダメージ計算
        level = attacker.level
        power = move.power

        base_damage = (((2 * level / 5 + 2) * power * A / D) / 50) + 2

        # 3️⃣ 補正計算
        modifier = (
            self.get_stab(attacker, move)
            * self.get_type_effectiveness(move, defender)
            * self.get_weather_modifier(move, battlefield)
            * self.get_screen_modifier(move, defender_side)
        )

        # 4️⃣ 乱数を考慮した最小・最大ダメージ
        min_damage = int(base_damage * modifier * 0.85)
        max_damage = int(base_damage * modifier * 1.00)

        return (min_damage, max_damage)