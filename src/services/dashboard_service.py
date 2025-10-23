# src/services/dashboard_service.py
from src.database.manager import DatabaseManager

class DashboardService:
    """ダッシュボード関連のビジネスロジックを担当するサービスクラス"""

    def get_dashboard_data(self):
        """ダッシュボードに必要なデータをまとめて取得する"""
        summary = self.get_dashboard_summary()
        opponent_ranking = self.get_opponent_pokemon_ranking()
        win_rate_by_opponent = self.get_win_rate_by_opponent()
        my_selection_rate = self.get_my_pokemon_selection_rate()
        selection_pattern_win_rate = self.get_selection_pattern_win_rate()
        battle_stats = self.get_battle_stats()

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
            "selection_pattern_win_rate": selection_pattern_win_rate,
            "battle_stats": battle_stats,
        }

    def get_selection_pattern_win_rate(self) -> list[dict]:
        """自分の選出パターン（3体）ごとの勝率を計算する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            query = """
                SELECT p.battle_id, p.pokemon_name, b.result
                FROM parties_log p
                JOIN battles b ON p.battle_id = b.battle_id
                WHERE p.is_opponent = 0 AND p.is_selected = 1
                ORDER BY p.battle_id, p.pokemon_name
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            patterns = {}
            from collections import defaultdict
            battle_selections = defaultdict(list)
            for row in rows:
                battle_selections[row['battle_id']].append(row['pokemon_name'])

            for battle_id, selection in battle_selections.items():
                if len(selection) == 3:
                    pattern = tuple(sorted(selection))
                    if pattern not in patterns:
                        patterns[pattern] = {'wins': 0, 'losses': 0, 'total': 0}
                    
                    # battlesテーブルから結果を取得（既にある情報を使う）
                    cursor.execute("SELECT result FROM battles WHERE battle_id = ?", (battle_id,))
                    result = cursor.fetchone()['result']

                    if result == '勝ち':
                        patterns[pattern]['wins'] += 1
                    elif result == '負け':
                        patterns[pattern]['losses'] += 1
                    patterns[pattern]['total'] += 1

            win_rate_list = []
            for pattern, data in patterns.items():
                win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
                win_rate_list.append({
                    'pattern': list(pattern),
                    'win_rate': round(win_rate, 1),
                    'total_matches': data['total']
                })

            return sorted(win_rate_list, key=lambda x: x['total_matches'], reverse=True)

    def get_my_pokemon_selection_rate(self) -> list[dict]:
        """自分のポケモンの選出率を計算する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            query = """
                SELECT 
                    pokemon_name, 
                    SUM(CASE WHEN is_selected = 1 THEN 1 ELSE 0 END) as selected_count,
                    COUNT(*) as total_count
                FROM parties_log
                WHERE is_opponent = 0
                GROUP BY pokemon_name
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            selection_rates = []
            for row in rows:
                rate = (row['selected_count'] / row['total_count'] * 100) if row['total_count'] > 0 else 0
                selection_rates.append({
                    'pokemon_name': row['pokemon_name'],
                    'selection_rate': round(rate, 1),
                    'selected_count': row['selected_count'],
                    'total_count': row['total_count']
                })
            
            return sorted(selection_rates, key=lambda x: x['selection_rate'], reverse=True)

    def get_win_rate_by_opponent(self) -> list[dict]:
        """相手のポケモンごとの勝率を計算する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            # このクエリは複雑になるため、複数ステップで実行するか、より洗練されたSQLが必要です。
            # ここでは簡略化のため、Pythonで処理します。
            cursor.execute("SELECT battle_id, pokemon_name FROM parties_log WHERE is_opponent = 1")
            opponent_pokemons = cursor.fetchall()
            
            cursor.execute("SELECT battle_id, result FROM battles")
            battle_results = {row['battle_id']: row['result'] for row in cursor.fetchall()}

            stats = {}
            for battle_id, name in opponent_pokemons:
                if name not in stats:
                    stats[name] = {'wins': 0, 'losses': 0, 'total': 0}
                
                result = battle_results.get(battle_id)
                if result == '勝ち':
                    stats[name]['wins'] += 1
                elif result == '負け':
                    stats[name]['losses'] += 1
                stats[name]['total'] += 1

            win_rate_list = []
            for name, data in stats.items():
                win_rate = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
                win_rate_list.append({
                    'pokemon_name': name,
                    'win_rate': round(win_rate, 1),
                    'total_matches': data['total']
                })
            
            return win_rate_list

    def get_dashboard_summary(self, season: int = None) -> dict:
        """ダッシュボードのサマリー情報を取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            # 勝率
            base_query = "SELECT result, COUNT(*) as count FROM battles"
            params = []
            if season:
                base_query += " WHERE season = ?"
                params.append(season)
            base_query += " GROUP BY result"
            
            cursor.execute(base_query, params)
            results = {row['result']: row['count'] for row in cursor.fetchall()}
            
            wins = results.get('勝ち', 0)
            losses = results.get('負け', 0)
            total = wins + losses
            win_rate = (wins / total * 100) if total > 0 else 0

            # ランク推移
            rank_query = "SELECT battle_date, my_rank FROM battles"
            rank_params = []
            if season:
                rank_query += " WHERE season = ?"
                rank_params.append(season)
            rank_query += " ORDER BY battle_date ASC"
            cursor.execute(rank_query, rank_params)
            rank_history = [{'date': row['battle_date'], 'rank': row['my_rank']} for row in cursor.fetchall() if row['my_rank'] is not None]

            return {
                "win_rate": round(win_rate, 1),
                "wins": wins,
                "losses": losses,
                "total_matches": total,
                "rank_history": rank_history
            }

    def get_opponent_pokemon_ranking(self, limit: int = 10) -> list[dict]:
        """相手のパーティによく含まれるポケモンのランキングを取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            query = """
                SELECT pokemon_name, COUNT(*) as count
                FROM parties_log
                WHERE is_opponent = 1
                GROUP BY pokemon_name
                ORDER BY count DESC
                LIMIT ?
            """
            cursor.execute(query, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_battle_stats(self) -> dict:
        """勝率などの統計データを計算して取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM battle_logs")
            total_matches = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as wins FROM battle_logs WHERE result = 'win'")
            total_wins = cursor.fetchone()['wins']

            win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

            return {
                "total_matches": total_matches,
                "total_wins": total_wins,
                "win_rate": round(win_rate, 1)
            }

    def get_customization_data(self, pokemon_name: str):
        """指定されたポケモンのカスタマイズランキングを取得する"""
        if not pokemon_name:
            raise ValueError("pokemon_name is required")
            
        return self.get_opponent_pokemon_customization_ranking(pokemon_name)

    def get_opponent_pokemon_customization_ranking(self, pokemon_name: str, limit: int = 5) -> dict:
        """指定された相手ポケモンの技、持ち物、テラスタイプの採用率ランキングを取得する。"""
        with DatabaseManager() as db:
            cursor = db.get_cursor()
            
            # pokemon_id を取得
            cursor.execute("SELECT pokemon_id FROM pokemons_log WHERE pokemon_name = ?", (pokemon_name,))
            pokemon_ids = [row['pokemon_id'] for row in cursor.fetchall()]
            if not pokemon_ids:
                return {'moves': [], 'items': [], 'terastal_types': []}

            placeholders = ', '.join('?' for _ in pokemon_ids)

            # 技
            # movesはJSON配列なので、この方法では集計できない。要件を見直すか、テーブル構造の変更が必要。
            # ここでは仮実装として、movesカラムのテキスト自体をカウントする。
            moves_query = f"""
                SELECT moves, COUNT(*) as count
                FROM pokemons_log
                WHERE pokemon_id IN ({placeholders}) AND moves IS NOT NULL
                GROUP BY moves
                ORDER BY count DESC
                LIMIT ?
            """
            cursor.execute(moves_query, pokemon_ids + [limit])
            moves = [dict(row) for row in cursor.fetchall()]

            # 持ち物
            items_query = f"""
                SELECT item, COUNT(*) as count
                FROM pokemons_log
                WHERE pokemon_id IN ({placeholders}) AND item IS NOT NULL
                GROUP BY item
                ORDER BY count DESC
                LIMIT ?
            """
            cursor.execute(items_query, pokemon_ids + [limit])
            items = [dict(row) for row in cursor.fetchall()]

            # テラスタイプ
            terastal_query = f"""
                SELECT terastal_type, COUNT(*) as count
                FROM pokemons_log
                WHERE pokemon_id IN ({placeholders}) AND terastal_type IS NOT NULL
                GROUP BY terastal_type
                ORDER BY count DESC
                LIMIT ?
            """
            cursor.execute(terastal_query, pokemon_ids + [limit])
            terastal_types = [dict(row) for row in cursor.fetchall()]

            return {
                'moves': moves,
                'items': items,
                'terastal_types': terastal_types
            }
