# src/ai/agent.py

import random
from src.core import calculator

class SimpleAgent:
    """単純なルールベースで行動を決定するAIエージェント。"""

    def __init__(self, party):
        self.party = party
        self.current_pokemon_index = 0
        self.log = []

    @property
    def current_pokemon(self):
        return self.party[self.current_pokemon_index]

    def choose_action(self, opponent_pokemon):
        """
        行動選択ロジック。
        1. 効果抜群の技があれば、その中で威力が最も高い技を選択。
        2. なければ、等倍以上の技をランダムに選択。
        3. 攻撃技がなければ、交代を試みる。
        """
        best_move = None
        max_effectiveness = 0
        highest_power = 0

        available_moves = [m for m in self.current_pokemon.get('moves', []) if m]

        if not available_moves:
            # 技がない場合、交代できるか試す
            return self.choose_switch(opponent_pokemon)

        for move in available_moves:
            # 相手のタイプ情報を取得。存在しない場合はデフォルト値（例：'normal'）を使うなど、エラーを防ぐ
            opponent_type1 = opponent_pokemon.get('type1', 'normal')
            opponent_type2 = opponent_pokemon.get('type2', None)
            
            effectiveness = calculator.type_chart.get_effectiveness(
                move['type'].lower(),
                [t.lower() for t in [opponent_type1, opponent_type2] if t]
            )

            # 効果抜群の技を優先
            if effectiveness > max_effectiveness:
                max_effectiveness = effectiveness
                highest_power = move.get('power', 0) or 0
                best_move = move
            # 同じ効果倍率なら威力を比較
            elif effectiveness == max_effectiveness:
                power = move.get('power', 0) or 0
                if power > highest_power:
                    highest_power = power
                    best_move = move
        
        # 有効な技が見つからなかった場合、ランダムに技を選ぶ
        if not best_move and available_moves:
            best_move = random.choice(available_moves)

        # 使える技がなければ交代
        if not best_move:
             return self.choose_switch(opponent_pokemon)

        return {'type': 'move', 'move': best_move}

    def choose_switch(self, opponent_pokemon):
        """交代先のポケモンを選択する。"""
        # HPが残っているポケモンを探す
        available_switches = [i for i, p in enumerate(self.party) if p['current_hp'] > 0 and i != self.current_pokemon_index]
        
        if not available_switches:
            return None # 交代不可

        # TODO: より賢い交代ロジックを実装
        # ここでは単純にリストの最初のポケモンを選択
        best_switch_index = available_switches[0]
        
        return {'type': 'switch', 'to_index': best_switch_index}

    def switch_pokemon(self, new_index):
        """ポケモンを交代させる。"""
        if 0 <= new_index < len(self.party) and self.party[new_index]['current_hp'] > 0:
            self.current_pokemon_index = new_index
            self.log.append(f"エージェントは {self.current_pokemon['pokemon_name']} に交代した。")
            return True
        return False
