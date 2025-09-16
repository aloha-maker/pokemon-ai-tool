import random
import sqlite3
import os
from collections import Counter
from ..core.type_chart import TYPE_EFFECTIVENESS

# データベースファイルのパスをプロジェクトルートからの相対パスで解決
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "pokemon_ai.db")

class PartyGenerator:
    """
    ユーザーの入力に基づき、コンセプトに沿ったパーティと運用ガイドを生成するクラス。
    """
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def _get_pokemon_data(self, pokemon_names: list) -> list:
        """指定されたポケモン名のリストの完全なデータをDBから取得する"""
        cursor = self.conn.cursor()
        # プレースホルダーの文字列を生成: (?, ?, ?, ...)
        placeholders = ', '.join('?' for _ in pokemon_names)
        query = f"SELECT * FROM pokemons WHERE name_ja IN ({placeholders})"
        cursor.execute(query, pokemon_names)
        return [dict(row) for row in cursor.fetchall()]

    def _get_pokemon_role(self, stats: dict) -> str:
        """ステータスに基づいてポケモンの役割を判定する"""
        hp, attack, defense, sp_attack, sp_defense, speed = stats['hp'], stats['attack'], stats['defense'], stats['sp_attack'], stats['sp_defense'], stats['speed']
        
        if speed > 100 and (attack > 100 or sp_attack > 100):
            return "高速アタッカー"
        if (defense > 110 and hp > 80) or (sp_defense > 110 and hp > 80):
            return "耐久型"
        if attack > 120 or sp_attack > 120:
            return "高火力アタッカー"
        if speed < 50 and (attack > 90 or sp_attack > 90):
            return "トリックルームアタッカー"
        return "バランス型"

    def _get_party_weaknesses(self, party: list) -> Counter:
        """パーティ全体の弱点を集計する"""
        weaknesses = Counter()
        for pokemon in party:
            my_types = [pokemon['type1'], pokemon['type2']]
            for attack_type, effectiveness_map in TYPE_EFFECTIVENESS.items():
                multiplier = 1.0
                for my_type in my_types:
                    if my_type:
                        multiplier *= effectiveness_map.get(my_type, 1.0)
                if multiplier >= 2.0:
                    weaknesses[attack_type] += 1
        return weaknesses

    def generate(self, available_pokemon_names: list, concept: str):
        """
        パーティと運用ガイドを生成するメインメソッド。
        """
        if len(available_pokemon_names) < 6:
            return {"error": "使用可能なポケモンが6体未満です。"}

        # 1. 利用可能なポケモンの詳細データを取得
        all_pokemon_data = self._get_pokemon_data(available_pokemon_names)
        if len(all_pokemon_data) < 6:
            return {"error": "データベースに登録されているポケモンが6体未満です。"}

        # 2. 各ポケモンに役割を付与
        for p in all_pokemon_data:
            p['role'] = self._get_pokemon_role(p)

        # 3. コンセプトに基づいて候補をフィルタリング
        candidates = []
        if "対面" in concept or "アタッカー" in concept:
            candidates = [p for p in all_pokemon_data if "アタッカー" in p['role']]
        elif "受け" in concept or "サイクル" in concept or "耐久" in concept:
            candidates = [p for p in all_pokemon_data if p['role'] == "耐久型"]
        else: # バランス
            candidates = all_pokemon_data
        
        # 候補が6体未満の場合は元のリストに戻す
        if len(candidates) < 6:
            candidates = all_pokemon_data
        
        random.shuffle(candidates)

        # 4. パーティを構築 (タイプバランスを考慮)
        party = []
        party_names = set()

        # 最初の1体はコンセプトに最も合うものからランダムに選ぶ
        if candidates:
            first_pokemon = random.choice(candidates)
            party.append(first_pokemon)
            party_names.add(first_pokemon['name_ja'])

        # 残りの5体を選ぶ
        while len(party) < 6:
            weaknesses = self._get_party_weaknesses(party)
            best_candidate = None
            best_score = -1

            # 候補の中から、現在のパーティの弱点を最もカバーできるポケモンを探す
            for candidate in all_pokemon_data:
                if candidate['name_ja'] in party_names: continue
                
                score = 0
                candidate_types = [candidate['type1'], candidate['type2']]
                # 弱点タイプに耐性があればスコア加算
                for weak_type, count in weaknesses.items():
                    for cand_type in candidate_types:
                        if cand_type and TYPE_EFFECTIVENESS[weak_type].get(cand_type, 1.0) < 1.0:
                            score += count # 弱点の数だけスコアを高くする
                
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
            
            if best_candidate:
                party.append(best_candidate)
                party_names.add(best_candidate['name_ja'])
            else:
                # 万が一候補が見つからなければランダムに追加してループを抜ける
                remaining = [p for p in all_pokemon_data if p['name_ja'] not in party_names]
                party.extend(random.sample(remaining, 6 - len(party)))
                break

        # 5. 詳細と運用ガイドを生成
        party_details = []
        for p_data in party:
            party_details.append({
                "name": p_data['name_ja'],
                "item": "たべのこし", # ダミー
                "ability": "", # ダミー
                "terastal_type": "ノーマル", # ダミー
                "moves": ["技1", "技2", "技3", "技4"], # ダミー
                "role": p_data['role']
            })

        manual = self._generate_manual(concept, party_details)

        return {
            "party": party_details,
            "manual": manual
        }

    def _generate_manual(self, concept: str, party_details: list) -> str:
        """パーティ構成とコンセプトに基づいて運用ガイドを生成する"""
        manual = f"### 「{concept}」コンセプト 構築ガイド\n\n"
        manual += "この構築は、指定されたコンセプトとタイプバランスを重視して選出されています。\n\n"
        
        attackers = [p for p in party_details if "アタッカー" in p['role']]
        tanks = [p for p in party_details if "耐久" in p['role']]

        if attackers:
            manual += f"**基本選出**: {attackers[0]['name']} + {attackers[1]['name'] if len(attackers) > 1 else random.choice(party_details)['name']} + {random.choice(party_details)['name']}\n"
        elif tanks:
            manual += f"**基本選出**: {tanks[0]['name']} + {tanks[1]['name'] if len(tanks) > 1 else random.choice(party_details)['name']} + {random.choice(party_details)['name']}\n"
        else:
            manual += f"**基本選出**: {party_details[0]['name']} + {party_details[1]['name']} + {party_details[2]['name']}\n"

        manual += "\n**立ち回り**: \n"
        if "対面" in concept:
            manual += "個々のポケモンの対面性能を活かし、有利な相手に積極的に攻撃を仕掛けていくのが基本戦術です。サイクルは最小限に留め、目の前の相手を倒すことを意識しましょう。"
        elif "受け" in concept or "サイクル" in concept:
            manual += "タイプ相性や耐久力を活かして相手の攻撃を受け止め、有利な対面を作り出すサイクル戦が基本です。相手の交代を読み、こちらも交代を合わせていくことが重要になります。"
        else:
            manual += "状況に応じて、攻撃的な選出とサイクル重視の選出を使い分けましょう。相手のパーティを見て、どのポケモンが刺さっているかを見極めることが重要です。"
        
        return manual

    def __del__(self):
        self.conn.close()