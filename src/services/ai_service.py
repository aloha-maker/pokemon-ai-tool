# src/services/ai_service.py
from typing import List, Dict, Any
from src.ai.party_generator import PartyGenerator
from src.ai.win_rate_predictor import WinRatePredictor
from src.services.party_service import PartyService

class AiService:
    """AI関連のビジネスロジックを担当する"""

    def predict_best_team(self, my_party: List[str] = None, my_party_id: int = None, opponent_party: List[str] = None) -> Dict[str, Any]:
        """最適な選出と勝率を予測する"""
        my_party_from_db = []
        if my_party_id:
            party_service = PartyService()
            my_party_from_db = party_service.get_by_id(my_party_id)
        else:
            my_party_from_db = my_party or []

        opponent_party_list = opponent_party or []
        members = [row['name'] for row in my_party_from_db['members']]

        if len(members) != 6 or len(opponent_party_list) != 6:
            raise ValueError("パーティはそれぞれ6体入力してください。")

        # 注意: WinRatePredictorのインスタンス化はコストが高い可能性があるため、
        # 本来はシングルトンなどで管理することが望ましい。
        predictor = WinRatePredictor()
        result = predictor.predict_best_team(members, opponent_party_list)
        
        if 'error' in result:
            # AIロジック内で発生したエラー
            raise ValueError(result['error'])

        return result

    def generate_party(self, available_pokemon: List[str], concept: str) -> Dict[str, Any]:
        """指定された条件でパーティを生成する"""
        if not available_pokemon or not concept:
            raise ValueError("使用可能なポケモンと戦術コンセプトを入力してください。")

        generator = PartyGenerator()
        result = generator.generate(available_pokemon, concept)

        if 'error' in result:
            # AIロジック内で発生したエラー
            raise ValueError(result['error'])
            
        return result
