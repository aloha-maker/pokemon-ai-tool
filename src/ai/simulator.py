# src/ai/simulator.py

from src.ai.agent import SimpleAgent
from src.core import calculator
import copy

class BattleSimulator:
    """2つのパーティ間の対戦をシミュレートするクラス。"""

    def __init__(self, party1_data, party2_data):
        """
        シミュレータを初期化する。

        Args:
            party1_data (dict): パーティ1の情報（パーティ管理機能から取得した形式）
            party2_data (dict): パーティ2の情報
        """
        self.party1 = self._prepare_party(party1_data)
        self.party2 = self._prepare_party(party2_data)
        self.agent1 = SimpleAgent(self.party1)
        self.agent2 = SimpleAgent(self.party2)
        self.log = []
        self.turn_count = 0

    def _prepare_party(self, party_data):
        """シミュレーション用にパーティデータを初期化する。"""
        prepared_party = []
        for member in party_data['members']:
            # シミュレーション中に変更される可能性のある値（HPなど）をコピー
            sim_member = copy.deepcopy(member)
            # TODO: ステータス計算機能を使って正確なHPをセットする
            sim_member['current_hp'] = member.get('stats', {}).get('hp', 300) 
            sim_member['max_hp'] = member.get('stats', {}).get('hp', 300)
            prepared_party.append(sim_member)
        return prepared_party

    def run(self):
        """シミュレーションを実行する。"""
        self.log.append(f"対戦開始！")
        self.log.append(f"パーティ1: {[p['pokemon_name'] for p in self.party1]}")
        self.log.append(f"パーティ2: {[p['pokemon_name'] for p in self.party2]}")
        self.log.append("---")

        while not self._is_battle_over():
            self.turn_count += 1
            self.log.append(f"【ターン {self.turn_count}】")
            self._execute_turn()
            self.log.append("---")

        winner = self._get_winner()
        self.log.append(f"対戦終了！ 勝者: {winner}")
        return self.log

    def _execute_turn(self):
        """1ターン分の処理を実行する。"""
        p1 = self.agent1.current_pokemon
        p2 = self.agent2.current_pokemon
        self.log.append(f"エージェント1は {p1['pokemon_name']} を選択。")
        self.log.append(f"エージェント2は {p2['pokemon_name']} を選択。")

        # 1. 行動選択
        action1 = self.agent1.choose_action(p2)
        action2 = self.agent2.choose_action(p1)

        # 2. 行動順決定 (素早さ比較)
        # TODO: 正確なステータスを使って比較する
        p1_speed = p1.get('stats', {}).get('speed', 100)
        p2_speed = p2.get('stats', {}).get('speed', 100)

        if p1_speed >= p2_speed:
            first_agent, second_agent = self.agent1, self.agent2
            first_action, second_action = action1, action2
        else:
            first_agent, second_agent = self.agent2, self.agent1
            first_action, second_action = action2, action1
        
        self.log.append(f"{first_agent.current_pokemon['pokemon_name']} の方が速い！")

        # 3. 行動実行
        self._process_action(first_agent, second_agent, first_action)
        if not self._is_battle_over():
            self._process_action(second_agent, first_agent, second_action)

    def _process_action(self, attacker_agent, defender_agent, action):
        """エージェントの行動を処理する。"""
        if action is None:
            self.log.append(f"{attacker_agent.current_pokemon['pokemon_name']} は何もできなかった！")
            return

        if action['type'] == 'move':
            move = action['move']
            attacker = attacker_agent.current_pokemon
            defender = defender_agent.current_pokemon
            
            self.log.append(f"{attacker['pokemon_name']} の {move['name']}！")

            # TODO: ダメージ計算を実装
            damage = random.randint(30, 50) # 仮のダメージ
            defender['current_hp'] = max(0, defender['current_hp'] - damage)
            
            self.log.append(f"{defender['pokemon_name']} に {damage} のダメージ！ (残りHP: {defender['current_hp']}) ")

            if defender['current_hp'] == 0:
                self.log.append(f"{defender['pokemon_name']} は倒れた！")
                # 倒された側のエージェントが交代を選択
                switch_action = defender_agent.choose_switch(attacker)
                if switch_action:
                    self._process_action(defender_agent, attacker_agent, switch_action)
                
        elif action['type'] == 'switch':
            to_index = action['to_index']
            attacker_agent.current_pokemon_index = to_index
            self.log.append(f"{attacker_agent.party[to_index]['pokemon_name']} に交代した。")

    def _is_battle_over(self):
        """どちらかのパーティが全滅したか判定する。"""
        party1_fainted = all(p['current_hp'] <= 0 for p in self.party1)
        party2_fainted = all(p['current_hp'] <= 0 for p in self.party2)
        return party1_fainted or party2_fainted

    def _get_winner(self):
        """勝者を判定する。"""
        party1_fainted = all(p['current_hp'] <= 0 for p in self.party1)
        if party1_fainted:
            return "パーティ2"
        return "パーティ1"
