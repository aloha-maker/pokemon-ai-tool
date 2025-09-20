from typing import List, Dict

class TurnReconstructor:
    """
    OCRで抽出された一連のゲーム状態(state)から、
    意味のあるターンごとの対戦ログを再構築するクラス。
    """

    def reconstruct(self, extracted_states: List[Dict]) -> Dict:
        """
        抽出された状態のリストを受け取り、battle_log_schema.jsonの形式に変換する。

        Args:
            extracted_states: VideoProcessorによって抽出された状態のリスト。
                              各要素は {"frame": frame_number, "state": {...}} の形式。

        Returns:
            再構築された対戦ログ。battle_log_schema.jsonに準拠する。
        """
        if not extracted_states:
            return {"turns": []}

        # TODO: 実際のターン再構築ロジックをここに実装する
        # - 状態間の差分を詳細に分析する
        # - 「技の選択」「ポケモンの交代」「ダメージの発生」などのイベントを特定する
        # - イベントを時系列に並べ、1ターンごとのアクションにまとめる

        # 現段階では、ユニークな盤面のスナップショットを返すダミー実装
        unique_turns = []
        last_state_summary = None

        for i, data in enumerate(extracted_states):
            state = data['state']
            
            # 盤面を要約した文字列を作成（比較用）
            current_state_summary = f"{state.get('my_pokemon_name')}-{state.get('opponent_pokemon_name')}"

            if current_state_summary != last_state_summary:
                turn_log = {
                    "turn": len(unique_turns) + 1,
                    "my_pokemon": state.get('my_pokemon_name'),
                    "my_pokemon_hp": state.get('my_pokemon_hp'),
                    "opponent_pokemon": state.get('opponent_pokemon_name'),
                    "opponent_pokemon_hp": state.get('opponent_pokemon_hp'),
                    "action": {
                        "type": "move", # ダミー
                        "name": "(技不明)", # ダミー
                    },
                    "log_text": f"Frame {data['frame']} の盤面スナップショット"
                }
                unique_turns.append(turn_log)
                last_state_summary = current_state_summary

        return {"turns": unique_turns}
