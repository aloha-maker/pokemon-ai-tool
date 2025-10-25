import random
from collections import Counter
from ..core.type_chart import TYPE_EFFECTIVENESS
from ..services.master_data_service import MasterDataService

class PartyGenerator:
    """
    ユーザーの入力に基づき、コンセプトに沿ったパーティと運用ガイドを生成するクラス。
    """
    def __init__(self):
        self.master_data_service = MasterDataService()
        self.all_abilities = self.master_data_service.get_master_data_by_resource('abilities')
        self.all_items = self.master_data_service.get_master_data_by_resource('items')
        self.all_natures = self.master_data_service.get_master_data_by_resource('natures')
        self.all_types = self.master_data_service.get_master_data_by_resource('types')

    def _get_pokemon_data(self, pokemon_names: list) -> list:
        """指定されたポケモン名のリストの完全なデータをDBから取得する"""
        return self.master_data_service.get_pokemons_by_names(pokemon_names)

    def _get_pokemon_role(self, stats: dict) -> str:
        """ステータスに基づいてポケモンの役割を判定する"""
        hp, attack, defense, sp_attack, sp_defense, speed = stats['hp'], stats['attack'], stats['defense'], stats['sp_attack'], stats['sp_defense'], stats['speed']
        
        if speed > 100 and (attack > 100 or sp_attack > 100):
            return "高速アタッカー"
        if (defense > 110 and hp > 80) or (sp_defense > 110 and hp > 80):
            return "物理受け" if defense > sp_defense else "特殊受け"
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

    def _choose_ability(self, p_data: dict) -> dict:
        """ポケモンに紐づく正しい特性の中からランダムに1つ選択する"""
        possible_abilities = self.master_data_service.get_abilities_by_pokemon_id(p_data['id'])
        return random.choice(possible_abilities)

    def _choose_item(self, p_data: dict, role: str) -> dict:
        role_items = {
            "高速アタッカー": ["こだわりスカーフ", "いのちのたま", "きあいのタスキ"],
            "高火力アタッカー": ["こだわりハチマキ", "こだわりメガネ", "いのちのたま"],
            "物理受け": ["ゴツゴツメット", "たべのこし", "オボンのみ"],
            "特殊受け": ["とつげきチョッキ", "たべのこし", "オボンのみ"],
            "トリックルームアタッカー": ["いのちのたま", "くろいてっきゅう"],
            "バランス型": ["たべのこし", "オボンのみ", "とつげきチョッキ"]
        }
        item_name = random.choice(role_items.get(role, ["たべのこし"]))
        return next((item for item in self.all_items if item['name_ja'] == item_name), self.all_items[0])

    def _choose_nature(self, p_data: dict, role: str) -> dict:
        physical_attacker_natures = ["いじっぱり", "ようき"] # Attack+, Sp. Atk- | Speed+, Sp. Atk-
        special_attacker_natures = ["ひかえめ", "おくびょう"] # Sp. Atk+, Attack- | Speed+, Attack-
        
        nature_name = "がんばりや" # Default
        if "アタッカー" in role:
            if p_data['attack'] > p_data['sp_attack']:
                nature_name = random.choice(physical_attacker_natures)
            else:
                nature_name = random.choice(special_attacker_natures)
        elif "受け" in role:
            if "物理" in role:
                nature_name = "ずぶとい" # Defense+, Attack-
            else:
                nature_name = "おだやか" # Sp. Def+, Attack-

        return next((n for n in self.all_natures if n['name_ja'] == nature_name), self.all_natures[0])

    def _generate_evs(self, role: str, nature: dict) -> dict:
        evs = {'ev_hp': 0, 'ev_atk': 0, 'ev_def': 0, 'ev_spa': 0, 'ev_spd': 0, 'ev_spe': 0}
        if "アタッカー" in role:
            if nature['increased_stat'] == 'attack':
                evs['ev_atk'] = 252
                evs['ev_spe'] = 252
            elif nature['increased_stat'] == 'sp_attack':
                evs['ev_spa'] = 252
                evs['ev_spe'] = 252
            else: # Speed boosting nature
                evs['ev_spe'] = 252
                if nature['decreased_stat'] == 'sp_attack':
                     evs['ev_atk'] = 252
                else:
                     evs['ev_spa'] = 252
        elif "受け" in role:
            evs['ev_hp'] = 252
            if "物理" in role:
                evs['ev_def'] = 252
            else:
                evs['ev_spd'] = 252
        
        # 残りはHPに4
        if sum(evs.values()) == 504:
            evs['ev_hp'] = 4

        return evs

    def _choose_moves(self, p_data: dict) -> list[dict]:
        moves = []
        is_physical = p_data['attack'] > p_data['sp_attack']
        category = "物理" if is_physical else "特殊"

        # STAB moves
        for move_type in [p_data['type1'], p_data['type2']]:
            if move_type and len(moves) < 2:
                stab_moves = self.master_data_service.get_moves_by_type(move_type, category)
                if stab_moves:
                    moves.append(random.choice(stab_moves))
        
        # Coverage moves
        coverage_types = ["ノーマル", "じめん", "ほのお", "こおり", "でんき"]
        while len(moves) < 4:
            move_type = random.choice(coverage_types)
            # 同じタイプの技は避ける
            if any(m['type'] == move_type for m in moves):
                continue
            
            coverage_moves = self.master_data_service.get_moves_by_type(move_type, category)
            if coverage_moves:
                moves.append(random.choice(coverage_moves))
            else:
                # 見つからなければループを抜ける
                break
        
        # 技が4つに満たない場合、全技からランダムに補充（ダミー）
        while len(moves) < 4:
            moves.append({'id': 1, 'name_ja': 'わるあがき'})

        return moves

    def generate(self, available_pokemon_names: list, concept: str):
        """
        パーティと運用ガイドを生成するメインメソッド。
        """
        if len(available_pokemon_names) < 6:
            return {"error": "使用可能なポケモンが6体未満です。"}

        all_pokemon_data = self._get_pokemon_data(available_pokemon_names)
        if len(all_pokemon_data) < 6:
            found_names = {p['name_ja'] for p in all_pokemon_data} | {p['name'] for p in all_pokemon_data}
            missing_names = [name for name in available_pokemon_names if name not in found_names]
            if missing_names:
                return {"error": f"データベースにポケモンが見つかりません: {', '.join(missing_names)}"}
            return {"error": "データベースに登録されているポケモンが6体未満です。"}

        for p in all_pokemon_data:
            p['role'] = self._get_pokemon_role(p)

        candidates = []
        if "対面" in concept or "アタッカー" in concept:
            candidates = [p for p in all_pokemon_data if "アタッカー" in p['role']]
        elif "受け" in concept or "サイクル" in concept or "耐久" in concept:
            candidates = [p for p in all_pokemon_data if "受け" in p['role']]
        else: # バランス
            candidates = all_pokemon_data
        
        if len(candidates) < 6:
            candidates = all_pokemon_data
        
        random.shuffle(candidates)

        party = []
        party_names = set()

        if candidates:
            first_pokemon = random.choice(candidates)
            party.append(first_pokemon)
            party_names.add(first_pokemon['name_ja'])

        while len(party) < 6:
            weaknesses = self._get_party_weaknesses(party)
            best_candidate = None
            best_score = -1

            for candidate in all_pokemon_data:
                if candidate['name_ja'] in party_names: continue
                
                score = 0
                candidate_types = [candidate['type1'], candidate['type2']]
                for weak_type, count in weaknesses.items():
                    for cand_type in candidate_types:
                        if cand_type and TYPE_EFFECTIVENESS[weak_type].get(cand_type, 1.0) < 1.0:
                            score += count
                
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
            
            if best_candidate:
                party.append(best_candidate)
                party_names.add(best_candidate['name_ja'])
            else:
                remaining = [p for p in all_pokemon_data if p['name_ja'] not in party_names]
                party.extend(random.sample(remaining, 6 - len(party)))
                break

        party_details = []
        for p_data in party:
            role = p_data['role']
            nature = self._choose_nature(p_data, role)
            item = self._choose_item(p_data, role)
            ability = self._choose_ability(p_data)
            evs = self._generate_evs(role, nature)
            moves = self._choose_moves(p_data)
            
            tera_type_name = random.choice([p_data['type1'], p_data.get('type2') or p_data['type1']])
            tera_type = next((t for t in self.all_types if t['name'] == tera_type_name), self.all_types[0])

            party_details.append({
                "pokemon_id": p_data['id'],
                "name": p_data['name_ja'],
                "item_id": item['id'],
                "item_name": item['name_ja'],
                "ability_id": ability['id'],
                "ability_name": ability['name_ja'],
                "nature_id": nature['id'],
                "nature_name": nature['name_ja'],
                "tera_type_id": tera_type['id'],
                "tera_type_name": tera_type['name_ja'],
                "evs": evs,
                "moves": [
                    {"id": m.get('id'), "name": m.get('name_ja')} for m in moves
                ],
                "role": role
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
        tanks = [p for p in party_details if "受け" in p['role']]

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