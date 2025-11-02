"""
修正版 calculate.py - ダメージ計算（クラス版）
"""
import random
import json
import copy
from pathlib import Path
import numpy as np
from typing import Literal, Optional, Tuple

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

    def simulate_team_damage(
        self,
        battle_state: BattleState
    ) -> dict:
        """
        攻撃側のアクティブポケモンが持つ全技について、
        相手チーム全員に対するダメージをシミュレーションする。

        Returns:
            dict: {move_name: {defender_name: {"min": int, "max": int, "effectiveness": float}}}
        """

        attacker_side = battle_state.get_attacker_side()
        attacker = attacker_side.active
        results = {}

        for move in attacker.moves:
            move_result = {}

            for defender in battle_state.get_defender_side().team:
                # 🔸 deepcopyで battle_state のコピーを作成
                sim_state = copy.deepcopy(battle_state)

                # コピー上で防御側を切り替える
                sim_defender_side = sim_state.get_defender_side()
                sim_defender_side.set_active(defender)
                sim_state.update_sides(sim_state.get_attacker_side(), sim_defender_side)

                # ダメージ計算
                min_dmg, max_dmg = self.calculate_damage(move, sim_state)
                effectiveness = self.get_type_effectiveness(move, defender)

                move_result[defender.name] = {
                    "min": min_dmg,
                    "max": max_dmg,
                    "effectiveness": effectiveness,
                    "percent_min": round(min_dmg / defender.max_hp * 100, 1),
                    "percent_max": round(max_dmg / defender.max_hp * 100, 1),
                }

            results[move.name] = move_result

        return results

    def estimate_ev_from_damage(
        self,
        move: "Move",
        battle_state: "BattleState",
        observed_damage: Tuple[int, int],
        target: Literal["attacker", "defender"] = "defender",
        step: int = 4,
    ) -> Optional[dict]:
        """
        実測ダメージ範囲から攻撃/防御努力値を推定する。
        既存の calculate_damage() が (min, max) を返す設計に対応。

        Parameters
        ----------
        move : Move
            技情報
        battle_state : BattleState
            現在のバトル状態（attacker, defender含む）
        observed_damage : (min, max)
            実際に観測されたダメージ範囲
        target : "attacker" | "defender"
            どちらの努力値を推定するか
        step : int
            探索ステップ幅（通常4）

        Returns
        -------
        dict or None
            {"estimated_ev": int, "range": (min_ev, max_ev), "detail": [...]} 形式
        """

        candidates = []

        attacker = battle_state.get_attacker_side().active
        defender = battle_state.get_defender_side().active

        for ev in range(0, 253, step):
            # 推定対象の努力値を更新
            if target == "attacker":
                if move.category == "physical":
                    attacker.ev["atk"] = ev
                else:
                    attacker.ev["spa"] = ev
            else:
                if move.category == "physical":
                    defender.ev["def"] = ev
                else:
                    defender.ev["spd"] = ev

            # その努力値でのダメージ範囲を取得
            dmg_min, dmg_max = self.calculate_damage(move, battle_state)

            # 観測範囲と重なるか判定
            obs_min, obs_max = observed_damage
            if dmg_max >= obs_min and dmg_min <= obs_max:
                candidates.append({
                    "ev": ev,
                    "calc_range": (dmg_min, dmg_max),
                })

        if not candidates:
            return None

        median_ev = int(np.median([c["ev"] for c in candidates]))
        return {
            "estimated_ev": median_ev,
            "range": (candidates[0]["ev"], candidates[-1]["ev"]),
            "num_candidates": len(candidates),
            "detail": candidates,
        }