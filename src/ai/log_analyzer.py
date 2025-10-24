# src/ai/log_analyzer.py

import json
from collections import Counter
from src.services.battle_service import BattleService

class LogAnalyzer:
    """
    battle_logsテーブルに蓄積された対戦データを分析するクラス。
    """

    def __init__(self):
        """
        初期化時にバトルサービスをインスタンス化する。
        """
        self.battle_service = BattleService()

    def get_all_logs(self) -> list[dict]:
        """
        すべての対戦ログを取得する。
        """
        return self.battle_service.get_all_battle_logs()

    def calculate_move_frequencies(self, pokemon_name: str) -> Counter:
        """
        指定されたポケモンが使用した技の頻度を計算する。
        """
        logs = self.get_all_logs()
        move_counter = Counter()

        for log in logs:
            if not log.get('battle_data') or not log['battle_data'].get('turns'):
                continue
            
            for turn in log['battle_data']['turns']:
                # 自分の行動ログのみを対象とする
                if turn.get('my_pokemon') == pokemon_name and turn.get('action', {}).get('type') == 'move':
                    move_name = turn['action'].get('name')
                    if move_name:
                        move_counter[move_name] += 1
        
        return move_counter

    def calculate_matchup_actions(self, my_pokemon: str, opponent_pokemon: str) -> dict:
        """
        指定された対面で取られた行動の統計を計算する。
        """
        logs = self.get_all_logs()
        action_counter = Counter()
        total_matchups = 0

        for log in logs:
            if not log.get('battle_data') or not log['battle_data'].get('turns'):
                continue

            for turn in log['battle_data']['turns']:
                # 指定された対面かチェック
                if (turn.get('my_pokemon') == my_pokemon and turn.get('opponent_pokemon') == opponent_pokemon):
                    total_matchups += 1
                    action = turn.get('action', {})
                    action_type = action.get('type')
                    action_name = action.get('name')
                    
                    if action_type and action_name:
                        # (move, イナズマドライブ) のような文字列をキーにする
                        action_key = f"{action_type}: {action_name}"
                        action_counter[action_key] += 1

        # 結果をパーセンテージに変換
        action_frequencies = {}
        if total_matchups > 0:
            action_frequencies = {act: (count / total_matchups) * 100 for act, count in action_counter.items()}

        results = {
            "my_pokemon": my_pokemon,
            "opponent_pokemon": opponent_pokemon,
            "total_matchups": total_matchups,
            "action_frequencies_percent": {k: round(v, 2) for k, v in action_frequencies.items()}
        }
        return results

    def analyze_teras_timing(self) -> dict:
        """
        テラスタルが使用されたタイミングとポケモンを分析する。
        """
        logs = self.get_all_logs()
        teras_events = []
        turn_counter = Counter()

        for log in logs:
            if not log.get('battle_data') or not log['battle_data'].get('turns'):
                continue
            
            for turn_data in log['battle_data']['turns']:
                action = turn_data.get('action', {})
                if action.get('type') == 'teras':
                    turn_number = turn_data.get('turn')
                    event = {
                        "log_id": log.get('id'),
                        "turn": turn_number,
                        "pokemon": turn_data.get('my_pokemon'),
                        "teras_type": action.get('name') # action.nameにテラスタイプが入ると想定
                    }
                    teras_events.append(event)
                    if turn_number:
                        turn_counter[turn_number] += 1
        
        return {
            "total_teras_count": len(teras_events),
            "events": teras_events,
            "turn_distribution": dict(turn_counter)
        }

def run_full_analysis():
    """
    アナライザを実行し、結果をコンソールに出力する。
    """
    analyzer = LogAnalyzer()
    all_logs = analyzer.get_all_logs()
    
    if not all_logs:
        print("分析対象の対戦ログがありません。")
        return

    # --- 1. 全ポケモンの技使用頻度を計算 ---
    print("--- 全ポケモンの技使用頻度 ---")
    all_my_pokemons = set()
    for log in all_logs:
        if log.get('battle_data') and log['battle_data'].get('turns'):
            for turn in log['battle_data']['turns']:
                if turn.get('my_pokemon'):
                    all_my_pokemons.add(turn['my_pokemon'])
    
    for pokemon in sorted(list(all_my_pokemons)):
        move_freq = analyzer.calculate_move_frequencies(pokemon)
        if move_freq:
            print(f"\n[ {pokemon} ]")
            for move, count in move_freq.most_common():
                print(f"  - {move}: {count}回")

    # --- 2. 代表的な対面の統計を計算 ---
    # TODO: 対戦ログから頻出する対面を自動的に抽出するロジックを追加する
    print("\n\n--- 代表的な対面分析 ---")
    # 仮の対面リスト
    sample_matchups = [
        ("ミライドン", "コライドン"),
        ("カイリュー", "サーフゴー"),
    ]
    for p1, p2 in sample_matchups:
        matchup_stats = analyzer.calculate_matchup_actions(p1, p2)
        print(f"\n[ {p1} vs {p2} ] (総遭遇回数: {matchup_stats['total_matchups']})")
        if matchup_stats['action_frequencies_percent']:
            for action, freq in matchup_stats['action_frequencies_percent'].items():
                print(f"  - {action}: {freq}%")
        else:
            print("  データなし")

    # --- 3. テラスタル使用分析 ---
    print("\n\n--- テラスタル使用分析 ---")
    teras_analysis = analyzer.analyze_teras_timing()
    print(f"総テラスタル使用回数: {teras_analysis['total_teras_count']}")
    if teras_analysis['turn_distribution']:
        print("ターン毎の使用回数:")
        for turn, count in sorted(teras_analysis['turn_distribution'].items()):
            print(f"  - ターン{turn}: {count}回")


if __name__ == '__main__':
    run_full_analysis()
