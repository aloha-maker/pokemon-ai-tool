# src/ai/simulator.py

import random
import copy
from src.ai.agent import SimpleAgent
from src.core import calculator

class BattleSimulator:
    """2つのパーティ間の対戦をシミュレートするクラス。ステップ実行に対応。"""

    def __init__(self, party1_data, party2_data, party1_id, party2_id):
        """シミュレータを初期化する。"""
        self.party1_id = party1_id
        self.party2_id = party2_id
        self.initial_party1 = self._prepare_party(party1_data)
        self.initial_party2 = self._prepare_party(party2_data)
        
        self.party1 = []
        self.party2 = []
        self.active_pokemon1 = None
        self.active_pokemon2 = None
        
        self.agent1 = None
        self.agent2 = None
        
        self.log = []
        self.turn_count = 0
        self.state = "INITIALIZED"  # INITIALIZED, SELECTING, READY_FOR_TURN, BATTLE_OVER
        self.winner = None

    def _prepare_party(self, party_data):
        """シミュレーション用にパーティデータを初期化する。"""
        prepared_party = []
        for member in party_data['members']:
            sim_member = copy.deepcopy(member)
            # TODO: ステータス計算を実装する
            # 仮のステータスを設定
            sim_member['stats'] = sim_member.get('stats', {
                'hp': 300, 'attack': 100, 'defense': 100, 
                'sp_attack': 100, 'sp_defense': 100, 'speed': 100
            })
            sim_member['current_hp'] = sim_member['stats']['hp']
            sim_member['max_hp'] = sim_member['stats']['hp']
            sim_member['moves'] = sim_member.get('moves', []) # movesがない場合のエラー回避
            prepared_party.append(sim_member)
        return prepared_party

    def start_selection(self):
        """選出フェーズを開始する。"""
        self.state = "SELECTING"
        self.log.append("対戦開始！ 各パーティから3体のポケモンを選出してください。")
        return self.get_state()

    def set_selection(self, selection1_indices, selection2_indices):
        """ユーザーの選出をセットし、バトルを開始する。"""
        if self.state != "SELECTING":
            raise Exception("Not in selection phase.")
        if len(selection1_indices) != 3 or len(selection2_indices) != 3:
            raise Exception("Each party must select 3 Pokemon.")

        self.party1 = [self.initial_party1[i] for i in selection1_indices]
        self.party2 = [self.initial_party2[i] for i in selection2_indices]

        self.agent1 = SimpleAgent(self.party1)
        self.agent2 = SimpleAgent(self.party2)
        
        self.active_pokemon1 = self.agent1.current_pokemon
        self.active_pokemon2 = self.agent2.current_pokemon

        self.state = "READY_FOR_TURN"
        self.log.append("---")
        self.log.append(f"パーティ1の選出: {[p['pokemon_name'] for p in self.party1]}")
        self.log.append(f"パーティ2の選出: {[p['pokemon_name'] for p in self.party2]}")
        self.log.append("---")
        self.log.append(f"最初の対面: {self.active_pokemon1['pokemon_name']} vs {self.active_pokemon2['pokemon_name']}")
        
        return self.get_state()

    def next_turn(self):
        """1ターン分の処理を実行する。"""
        if self.state != "READY_FOR_TURN":
            raise Exception("Not ready for next turn.")
        if self._is_battle_over():
            self.state = "BATTLE_OVER"
            self.winner = self._get_winner()
            self.log.append(f"対戦終了！ 勝者: {self.winner}")
            return self.get_state()

        self.turn_count += 1
        self.log.append(f"【ターン {self.turn_count}】")
        
        p1 = self.active_pokemon1
        p2 = self.active_pokemon2

        # 1. 行動選択
        action1 = self.agent1.choose_action(p2)
        action2 = self.agent2.choose_action(p1)

        # 2. 行動順決定
        p1_speed = p1['stats']['speed']
        p2_speed = p2['stats']['speed']

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
        
        self.log.append("---")

        if self._is_battle_over():
            self.state = "BATTLE_OVER"
            self.winner = self._get_winner()
            self.log.append(f"対戦終了！ 勝者: {self.winner}")

        return self.get_state()

    def _process_action(self, attacker_agent, defender_agent, action):
        """エージェントの行動を処理する。"""
        attacker = attacker_agent.current_pokemon
        defender = defender_agent.current_pokemon

        if attacker['current_hp'] <= 0:
            self.log.append(f"{attacker['pokemon_name']} はひんしで動けない！")
            return

        if action is None:
            self.log.append(f"{attacker['pokemon_name']} は何もできなかった！")
            return

        if action['type'] == 'move':
            move = action['move']
            self.log.append(f"{attacker['pokemon_name']} の {move['name']}！")

            # ダメージ計算
            # TODO: 本来はもっと詳細な情報が必要
            damage = calculator.calculate_damage_simple(
                attacker_stats=attacker['stats'],
                defender_stats=defender['stats'],
                move_power=move.get('power', 0) or 0, # powerがNoneの場合を考慮
            )
            defender['current_hp'] = max(0, defender['current_hp'] - damage)
            
            self.log.append(f"{defender['pokemon_name']} に {damage} のダメージ！ (残りHP: {defender['current_hp']}/{defender['max_hp']})")

            if defender['current_hp'] == 0:
                self.log.append(f"{defender['pokemon_name']} は倒れた！")
                # 倒された側のエージェントが交代を選択
                if not self._is_battle_over():
                    switch_action = defender_agent.choose_switch(attacker)
                    if switch_action:
                        self._process_action(defender_agent, attacker_agent, switch_action)
                    else:
                        # 交代先がいない場合は何もしない（全滅）
                        pass
                
        elif action['type'] == 'switch':
            to_index = action['to_index']
            attacker_agent.switch_pokemon(to_index)
            self.active_pokemon1 = self.agent1.current_pokemon
            self.active_pokemon2 = self.agent2.current_pokemon
            self.log.append(f"{attacker_agent.party[to_index]['pokemon_name']} に交代した。")

    def _is_battle_over(self):
        """どちらかのパーティが全滅したか判定する。"""
        party1_fainted = all(p['current_hp'] <= 0 for p in self.party1)
        party2_fainted = all(p['current_hp'] <= 0 for p in self.party2)
        return party1_fainted or party2_fainted

    def _get_winner(self):
        """勝者を判定する。"""
        if all(p['current_hp'] <= 0 for p in self.party1):
            return f"パーティ2 (ID: {self.party2_id})"
        if all(p['current_hp'] <= 0 for p in self.party2):
            return f"パーティ1 (ID: {self.party1_id})"
        return "不明"

    def get_state(self):
        """シミュレータの現在の状態を返す。"""
        return {
            "state": self.state,
            "turn_count": self.turn_count,
            "log": self.log,
            "winner": self.winner,
            "party1": {
                "id": self.party1_id,
                "pokemons": self.initial_party1 if self.state == "SELECTING" else self.party1,
                "active_pokemon_index": self.agent1.current_pokemon_index if self.agent1 else 0,
            },
            "party2": {
                "id": self.party2_id,
                "pokemons": self.initial_party2 if self.state == "SELECTING" else self.party2,
                "active_pokemon_index": self.agent2.current_pokemon_index if self.agent2 else 0,
            }
        }
