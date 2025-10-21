# src/services/dashboard_service.py
from src.database.manager import DatabaseManager

class DashboardService:
    """ダッシュボード関連のビジネスロジックを担当するサービスクラス"""

    def get_dashboard_data(self):
        """ダッシュボードに必要なデータをまとめて取得する"""
        with DatabaseManager() as db:
            summary = db.get_dashboard_summary()
            opponent_ranking = db.get_opponent_pokemon_ranking()
            win_rate_by_opponent = db.get_win_rate_by_opponent()
            my_selection_rate = db.get_my_pokemon_selection_rate()
            selection_pattern_win_rate = db.get_selection_pattern_win_rate()

            # 勝率が高い・低いで分類するロジック
            watch_out_pokemon = sorted(
                [p for p in win_rate_by_opponent if p['win_rate'] < 50], 
                key=lambda x: x['win_rate']
            )[:10]
            good_at_pokemon = sorted(
                [p for p in win_rate_by_opponent if p['win_rate'] >= 50], 
                key=lambda x: x['win_rate'], 
                reverse=True
            )[:10]

        return {
            "summary": summary,
            "opponent_ranking": opponent_ranking,
            "watch_out_pokemon": watch_out_pokemon,
            "good_at_pokemon": good_at_pokemon,
            "my_selection_rate": my_selection_rate,
            "selection_pattern_win_rate": selection_pattern_win_rate
        }

    def get_customization_data(self, pokemon_name: str):
        """指定されたポケモンのカスタマイズランキングを取得する"""
        if not pokemon_name:
            raise ValueError("pokemon_name is required")
            
        with DatabaseManager() as db:
            return db.get_opponent_pokemon_customization_ranking(pokemon_name)
