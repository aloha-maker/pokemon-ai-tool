import itertools
import os
from ..core.type_chart import get_effectiveness
from src.models import PokemonModel

class WinRatePredictor:
    """
    対戦前の選出フェーズで、有利な選出を予測・推薦するクラス。
    """
    def _get_pokemon_types(self, pokemon_name):
        """データベースからポケモン名に対応するタイプを取得する"""
        pokemon = PokemonModel.query.filter_by(name_ja=pokemon_name).first()
        if pokemon:
            return [t for t in [pokemon.type1, pokemon.type2] if t]
        return []

    def _calculate_matchup_score(self, my_types, opponent_types):
        """2匹のポケモン間のタイプ相性スコアを計算する"""
        score = 0
        # 攻撃面の評価: こちらの各タイプが相手に与える影響
        for my_type in my_types:
            eff = get_effectiveness(my_type, opponent_types)
            if eff >= 2.0: score += 2  # 効果は抜群
            if eff <= 0.5: score -= 1  # いまひとつ

        # 防御面の評価: 相手の各タイプがこちらに与える影響
        for opp_type in opponent_types:
            eff = get_effectiveness(opp_type, my_types)
            if eff >= 2.0: score -= 2  # 弱点を突かれる
            if eff <= 0.5: score += 1  # 耐性がある

        return score

    def predict_best_team(self, my_party_names, opponent_party_names):
        """
        与えられた両パーティから、最も有利な選出3体を予測する。

        Args:
            my_party_names (list[str]): 自パーティのポケモン名6体のリスト
            opponent_party_names (list[str]): 相手パーティのポケモン名6体のリスト

        Returns:
            dict: 最適な選出チームとスコア、またはエラーメッセージ
        """
        my_party_types = {name: self._get_pokemon_types(name) for name in my_party_names}
        opponent_party_types = {name: self._get_pokemon_types(name) for name in opponent_party_names}

        # DBに存在しないポケモンがいた場合のエラーハンドリング
        for name, types in {**my_party_types, **opponent_party_types}.items():
            if not types:
                return {"error": f"ポケモン「{name}」がデータベースに見つかりません。"}
        
        best_team = None
        best_score = -float('inf')

        # 自パーティから3体選出する全ての組み合わせを試行 (20通り)
        for team_combination in itertools.combinations(my_party_names, 3):
            current_team_score = 0
            # 選出した3体それぞれについて、相手パーティ全体との相性を評価
            for my_pokemon_name in team_combination:
                pokemon_score_vs_opponent_party = 0
                for opponent_pokemon_name in opponent_party_names:
                    my_types = my_party_types[my_pokemon_name]
                    opponent_types = opponent_party_types[opponent_pokemon_name]
                    
                    # 1対1の相性スコアを加算
                    pokemon_score_vs_opponent_party += self._calculate_matchup_score(my_types, opponent_types)
                
                current_team_score += pokemon_score_vs_opponent_party
            
            # ベストスコアを更新
            if current_team_score > best_score:
                best_score = current_team_score
                best_team = team_combination

        return {
            "recommended_team": list(best_team),
            "score": best_score,
            "reason": f"この選出は、相手パーティ全体に対して最も高い相性スコア({best_score})を獲得しました。"
        }
