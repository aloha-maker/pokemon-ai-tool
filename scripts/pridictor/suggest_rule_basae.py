from typing import List, Dict, Tuple, Optional
import json
from enum import Enum

class Weather(Enum):
    SUNNY = "晴れ"
    RAIN = "雨"
    SANDSTORM = "砂嵐"
    HAIL = "あられ"
    SNOW = "ゆき"
    ELECTRIC_TERRAIN = "エレキフィールド"
    PSYCHIC_TERRAIN = "サイコフィールド"
    GRASSY_TERRAIN = "グラスフィールド"
    MISTY_TERRAIN = "ミストフィールド"
    NONE = "なし"

class Hazard(Enum):
    STEALTH_ROCK = "ステルスロック"
    SPIKES = "まきびし"
    TOXIC_SPIKES = "どくびし"
    STICKY_WEB = "ねばねばネット"

class StatStage(Enum):
    SHARPLY_DROPPED = -2
    DROPPED = -1
    NORMAL = 0
    RISEN = 1
    SHARPLY_RISEN = 2

class PokemonState:
    def __init__(self, name: str, hp: float, max_hp: float = 100, ability: Optional[str] = None,
                 item: Optional[str] = None, status: Optional[str] = None, stat_stages: Dict[str, StatStage] = None):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.ability = ability
        self.item = item
        self.status = status
        
        if stat_stages is None:
            self.stat_stages = {
                "attack": StatStage.NORMAL,
                "defense": StatStage.NORMAL,
                "special_attack": StatStage.NORMAL,
                "special_defense": StatStage.NORMAL,
                "speed": StatStage.NORMAL,
                "accuracy": StatStage.NORMAL,
                "evasion": StatStage.NORMAL
            }
        else:
            self.stat_stages = stat_stages
    
    @property
    def hp_percentage(self) -> float:
        return (self.hp / self.max_hp) * 100
    
    def is_fainted(self) -> bool:
        return self.hp <= 0

class BattleState:
    def __init__(self, my_pokemon: PokemonState, opp_pokemon: PokemonState,
                 weather: Weather = Weather.NONE, terrain: str = "なし",
                 hazards_my_side: List[Hazard] = None, hazards_opp_side: List[Hazard] = None,
                 turn_count: int = 0, opponent_tendencies: Dict[str, float] = None):
        
        self.my_pokemon = my_pokemon
        self.opp_pokemon = opp_pokemon
        self.weather = weather
        self.terrain = terrain
        self.turn_count = turn_count
        
        if hazards_my_side is None:
            self.hazards_my_side = []
        else:
            self.hazards_my_side = hazards_my_side
            
        if hazards_opp_side is None:
            self.hazards_opp_side = []
        else:
            self.hazards_opp_side = hazards_opp_side
            
        if opponent_tendencies is None:
            self.opponent_tendencies = {}
        else:
            self.opponent_tendencies = opponent_tendencies

class RuleBasedAISuggest:
    """ルールベースのAIサジェストシステム"""
    
    # タイプ相性テーブル
    TYPE_EFFECTIVENESS = {
        "ノーマル": {"かくとう": 2.0, "ゴースト": 0.0},
        "ほのお": {"みず": 2.0, "じめん": 2.0, "いわ": 2.0, "くさ": 0.5, "こおり": 0.5, "むし": 0.5, "はがね": 0.5, "ほのお": 0.5},
        "みず": {"でんき": 2.0, "くさ": 2.0, "ほのお": 0.5, "みず": 0.5, "こおり": 0.5, "はがね": 0.5},
        "でんき": {"じめん": 2.0, "でんき": 0.5, "ひこう": 0.5, "はがね": 0.5},
        "くさ": {"ほのお": 2.0, "こおり": 2.0, "どく": 2.0, "ひこう": 2.0, "むし": 2.0, "みず": 0.5, "でんき": 0.5, "くさ": 0.5, "じめん": 0.5},
        "こおり": {"ほのお": 2.0, "かくとう": 2.0, "いわ": 2.0, "はがね": 2.0, "こおり": 0.5},
        "かくとう": {"ひこう": 2.0, "エスパー": 2.0, "フェアリー": 2.0, "むし": 0.5, "いわ": 0.5, "あく": 0.5},
        "どく": {"じめん": 2.0, "エスパー": 2.0, "くさ": 0.5, "かくとう": 0.5, "どく": 0.5, "むし": 0.5, "フェアリー": 0.5},
        "じめん": {"みず": 2.0, "くさ": 2.0, "こおり": 2.0, "どく": 0.5, "いわ": 0.5, "でんき": 0.0},
        "ひこう": {"でんき": 2.0, "こおり": 2.0, "いわ": 2.0, "かくとう": 0.5, "むし": 0.5, "くさ": 0.5, "じめん": 0.0},
        "エスパー": {"むし": 2.0, "あく": 2.0, "ゴースト": 2.0, "かくとう": 0.5, "エスパー": 0.5},
        "むし": {"ほのお": 2.0, "ひこう": 2.0, "いわ": 2.0, "くさ": 0.5, "かくとう": 0.5, "じめん": 0.5},
        "いわ": {"みず": 2.0, "くさ": 2.0, "かくとう": 2.0, "じめん": 2.0, "はがね": 2.0, "ノーマル": 0.5, "ほのお": 0.5, "どく": 0.5, "ひこう": 0.5},
        "ゴースト": {"ゴースト": 2.0, "あく": 2.0, "ノーマル": 0.0, "かくとう": 0.0},
        "ドラゴン": {"こおり": 2.0, "ドラゴン": 2.0, "フェアリー": 2.0, "ほのお": 0.5, "みず": 0.5, "でんき": 0.5, "くさ": 0.5},
        "あく": {"かくとう": 2.0, "むし": 2.0, "フェアリー": 2.0, "ゴースト": 0.5, "あく": 0.5, "エスパー": 0.0},
        "はがね": {"ほのお": 2.0, "かくとう": 2.0, "じめん": 2.0, "ノーマル": 0.5, "ひこう": 0.5, "いわ": 0.5, "むし": 0.5, "はがね": 0.5, "くさ": 0.5, "エスパー": 0.5, "こおり": 0.5, "ドラゴン": 0.5, "フェアリー": 0.5},
        "フェアリー": {"どく": 2.0, "はがね": 2.0, "かくとう": 0.5, "むし": 0.5, "あく": 0.5, "ドラゴン": 0.0}
    }
    
    # ポケモンのタイプデータ（簡易版）
    POKEMON_TYPES = {
        "ミライドン": ["でんき", "ドラゴン"],
        "コライドン": ["じめん", "ドラゴン"],
        "テツノワダチ": ["じめん", "はがね"],
        "バシャーモ": ["ほのお", "かくとう"],
        "イーユイ": ["あく", "ノーマル"],
        "サーナイト": ["エスパー", "フェアリー"],
        "カイリュー": ["ドラゴン", "ひこう"],
        "ガブリアス": ["ドラゴン", "じめん"],
        "サザンドラ": ["あく", "ドラゴン"],
        "ランドロス": ["じめん", "ひこう"],
        "サンダー": ["でんき", "ひこう"],
    }
    
    # 技のタイプデータ（簡易版）
    MOVE_TYPES = {
        "10まんボルト": "でんき",
        "かみなり": "でんき",
        "ボルトチェンジ": "でんき",
        "りゅうせいぐん": "ドラゴン",
        "りゅうのはどう": "ドラゴン",
        "だいちのちから": "じめん",
        "じしん": "じめん",
        "ストーンエッジ": "いわ",
        "インファイト": "かくとう",
        "かえんほうしゃ": "ほのお",
        "れいとうビーム": "こおり",
        "シャドーボール": "ゴースト",
        "サイコキネシス": "エスパー",
        "ムーンフォース": "フェアリー",
        "アイアンヘッド": "はがね",
        "ステルスロック": "いわ",
        "つるぎのまい": "ノーマル",
        "ロックカット": "ノーマル",
        "とつげき": "ノーマル",
    }
    
    def __init__(self):
        self.knowledge_base = self._build_knowledge_base()
    
    def _build_knowledge_base(self) -> Dict:
        """ドメイン知識ベースの構築"""
        return {
            "weather_effects": {
                "晴れ": {"ほのお": 1.5, "みず": 0.5},
                "雨": {"みず": 1.5, "ほのお": 0.5},
                "砂嵐": {"いわ": 1.5, "はがね": 1.5},
            },
            "terrain_effects": {
                "エレキフィールド": {"でんき": 1.3},
                "グラスフィールド": {"くさ": 1.3},
                "サイコフィールド": {"エスパー": 1.3},
                "ミストフィールド": {"ドラゴン": 0.5},
            },
            "ability_effects": {
                "かそく": {"speed_boost": True},
                "ちからもち": {"attack_boost": True},
                "てきおうりょく": {"type_effectiveness_boost": True},
                "ふゆう": {"ground_immunity": True},
                "ひひいろのこどう": {"sun_boost": True},
                "ハドロンエンジン": {"electric_terrain_boost": True},
            },
            "strategic_rules": {
                # 特定のポケモンに対する戦略
                "ミライドン_vs_コライドン": {
                    "avoid_moves": ["ドラゴン"],
                    "prefer_moves": ["でんき", "こおり", "フェアリー"],
                    "notes": "コライドンはじめんタイプなのででんき技が通らない。ドラゴン技は互いに効果ばつぐん"
                },
                "加速バシャーモ": {
                    "threat_level": "high",
                    "counter_strategy": "先制技や威嚇特性で対処",
                    "prefer_status_moves": True
                }
            }
        }
    
    def calculate_type_effectiveness(self, move_type: str, target_types: List[str]) -> float:
        """タイプ相性を計算"""
        if move_type not in self.TYPE_EFFECTIVENESS:
            return 1.0
        
        effectiveness = 1.0
        for target_type in target_types:
            if target_type in self.TYPE_EFFECTIVENESS[move_type]:
                effectiveness *= self.TYPE_EFFECTIVENESS[move_type][target_type]
        
        return effectiveness
    
    def evaluate_move(self, move: str, battle_state: BattleState, target_pokemon: str) -> Dict:
        """技の評価を実行"""
        if move not in self.MOVE_TYPES:
            return {"score": 0.5, "reason": "未知の技"}
        
        move_type = self.MOVE_TYPES[move]
        target_types = self.POKEMON_TYPES.get(target_pokemon, ["ノーマル"])
        
        # 基本スコア計算
        score = 1.0
        
        # タイプ相性
        type_effectiveness = self.calculate_type_effectiveness(move_type, target_types)
        score *= type_effectiveness
        
        # 天候補正
        weather = battle_state.weather.value
        if weather in self.knowledge_base["weather_effects"]:
            if move_type in self.knowledge_base["weather_effects"][weather]:
                score *= self.knowledge_base["weather_effects"][weather][move_type]
        
        # フィールド補正
        terrain = battle_state.terrain
        if terrain in self.knowledge_base["terrain_effects"]:
            if move_type in self.knowledge_base["terrain_effects"][terrain]:
                score *= self.knowledge_base["terrain_effects"][terrain][move_type]
        
        # 特性補正
        my_ability = battle_state.my_pokemon.ability
        if my_ability in self.knowledge_base["ability_effects"]:
            ability_effects = self.knowledge_base["ability_effects"][my_ability]
            if "electric_terrain_boost" in ability_effects and move_type == "でんき" and terrain == "エレキフィールド":
                score *= 1.3
        
        # 戦略的ルールの適用
        matchup_key = f"{battle_state.my_pokemon.name}_vs_{battle_state.opp_pokemon.name}"
        if matchup_key in self.knowledge_base["strategic_rules"]:
            rules = self.knowledge_base["strategic_rules"][matchup_key]
            if move_type in rules.get("avoid_moves", []):
                score *= 0.3
            if move_type in rules.get("prefer_moves", []):
                score *= 1.5
        
        # 状態による補正
        if hasattr(battle_state.opp_pokemon, 'stat_stages'):
            if battle_state.opp_pokemon.stat_stages["defense"].value > 0 and move_type in ["かくとう", "ノーマル"]:
                score *= 0.8  # 防御が上がっている場合、物理技の評価を下げる
        
        # ハザード考慮
        if hasattr(battle_state, 'hazards_opp_side'):
            if "ステルスロック" in [h.value for h in battle_state.hazards_opp_side]:
                # 岩ハザードがある場合、交代を促す可能性を考慮
                pass
        
        return {
            "move": move,
            "score": round(score, 2),
            "type_effectiveness": type_effectiveness,
            "reason": self._generate_reason(move, move_type, type_effectiveness, score)
        }
    
    def _generate_reason(self, move: str, move_type: str, effectiveness: float, score: float) -> str:
        """評価理由を生成"""
        reasons = []
        
        if effectiveness >= 2.0:
            reasons.append(f"{move_type}技は効果バツグン")
        elif effectiveness >= 1.0:
            reasons.append(f"{move_type}技は普通")
        elif effectiveness > 0.0:
            reasons.append(f"{move_type}技は今ひとつ")
        else:
            reasons.append(f"{move_type}技は通らない")
        
        if score > 1.5:
            reasons.append("非常に有利な状況")
        elif score > 1.0:
            reasons.append("有利な状況")
        elif score > 0.5:
            reasons.append("やや不利な状況")
        else:
            reasons.append("不利な状況")
        
        return "。".join(reasons)
    
    def suggest_moves(self, battle_state: BattleState, available_moves: List[str]) -> List[Dict]:
        """使用する技を提案"""
        suggestions = []
        
        for move in available_moves:
            evaluation = self.evaluate_move(move, battle_state, battle_state.opp_pokemon.name)
            suggestions.append(evaluation)
        
        # スコア順にソート
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        
        return suggestions
    
    def suggest_switch(self, battle_state: BattleState, available_pokemon: List[str]) -> List[Dict]:
        """交代先を提案"""
        suggestions = []
        
        current_matchup = f"{battle_state.my_pokemon.name}_vs_{battle_state.opp_pokemon.name}"
        
        for pokemon in available_pokemon:
            if pokemon == battle_state.my_pokemon.name:
                continue
            
            # 簡易的なタイプ相性評価
            my_types = self.POKEMON_TYPES.get(pokemon, ["ノーマル"])
            opp_types = self.POKEMON_TYPES.get(battle_state.opp_pokemon.name, ["ノーマル"])
            
            defense_score = 1.0
            for opp_type in opp_types:
                for my_type in my_types:
                    if my_type in self.TYPE_EFFECTIVENESS.get(opp_type, {}):
                        defense_score *= self.TYPE_EFFECTIVENESS[opp_type][my_type]
            
            # ハザードダメージ考慮
            hazard_damage_penalty = 0
            if hasattr(battle_state, 'hazards_my_side'):
                if "ステルスロック" in [h.value for h in battle_state.hazards_my_side]:
                    # 岩タイプかはがねタイプならダメージ軽減
                    if "いわ" not in my_types and "はがね" not in my_types:
                        hazard_damage_penalty = 0.2
            
            total_score = defense_score - hazard_damage_penalty
            
            suggestions.append({
                "pokemon": pokemon,
                "score": round(total_score, 2),
                "reason": f"防御相性: {defense_score}, ハザード考慮: {-hazard_damage_penalty}"
            })
        
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions
    
    def get_battle_analysis(self, battle_state: BattleState) -> Dict:
        """バトル状況の分析"""
        analysis = {
            "matchup_analysis": "",
            "threat_level": "medium",
            "recommended_strategy": "",
            "key_factors": []
        }
        
        # マッチアップ分析
        my_pokemon = battle_state.my_pokemon.name
        opp_pokemon = battle_state.opp_pokemon.name
        
        matchup_key = f"{my_pokemon}_vs_{opp_pokemon}"
        if matchup_key in self.knowledge_base["strategic_rules"]:
            rules = self.knowledge_base["strategic_rules"][matchup_key]
            analysis["matchup_analysis"] = rules.get("notes", "")
        
        # 脅威レベルの評価
        if hasattr(battle_state.opp_pokemon, 'stat_stages'):
            if battle_state.opp_pokemon.stat_stages["speed"].value > 0:
                analysis["threat_level"] = "high"
                analysis["key_factors"].append("相手の素早さが上昇中")
        
        if battle_state.opp_pokemon.ability == "かそく":
            analysis["threat_level"] = "very_high"
            analysis["key_factors"].append("加速特性に注意")
        
        # 戦略提案
        if analysis["threat_level"] == "very_high":
            analysis["recommended_strategy"] = "先制技や状態異常で対処を検討"
        elif battle_state.opp_pokemon.hp < 30:
            analysis["recommended_strategy"] = "とどめをさすチャンス"
        else:
            analysis["recommended_strategy"] = "タイプ有利技を選択"
        
        return analysis

# 使用例
def main():
    # サンプルのバトル状態を作成
    my_pokemon = PokemonState("ミライドン", 100)
    opp_pokemon = PokemonState("コライドン", 46)
    
    battle_state = BattleState(
        my_pokemon=my_pokemon,
        opp_pokemon=opp_pokemon,
        weather=Weather.SUNNY,
        terrain="エレキフィールド",
        hazards_opp_side=[Hazard.STEALTH_ROCK],
        turn_count=5
    )
    
    # AIサジェストシステムの初期化
    ai_suggest = RuleBasedAISuggest()
    
    # 使用可能な技
    available_moves = ["10まんボルト", "りゅうせいぐん", "だいちのちから", "ストーンエッジ"]
    
    # 技の提案
    move_suggestions = ai_suggest.suggest_moves(battle_state, available_moves)
    
    print("技の提案:")
    for suggestion in move_suggestions:
        print(f"  {suggestion['move']}: スコア {suggestion['score']} - {suggestion['reason']}")
    
    # 交代提案
    available_pokemon = ["ミライドン", "テツノワダチ", "イーユイ"]
    switch_suggestions = ai_suggest.suggest_switch(battle_state, available_pokemon)
    
    print("\n交代提案:")
    for suggestion in switch_suggestions:
        print(f"  {suggestion['pokemon']}: スコア {suggestion['score']}")
    
    # バトル分析
    analysis = ai_suggest.get_battle_analysis(battle_state)
    print(f"\nバトル分析:")
    print(f"  脅威レベル: {analysis['threat_level']}")
    print(f"  推奨戦略: {analysis['recommended_strategy']}")
    print(f"  主要要因: {', '.join(analysis['key_factors'])}")

if __name__ == "__main__":
    main()