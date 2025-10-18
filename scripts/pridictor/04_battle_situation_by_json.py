import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import os

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

@dataclass
class PokemonState:
    name: str
    hp: float
    max_hp: float = 100
    ability: Optional[str] = None
    item: Optional[str] = None
    status: Optional[str] = None
    stat_stages: Dict[str, StatStage] = None
    
    def __post_init__(self):
        if self.stat_stages is None:
            self.stat_stages = {
                "attack": StatStage.NORMAL,
                "defense": StatStage.NORMAL,
                "special_attack": StatStage.NORMAL,
                "special_defense": StatStage.NORMAL,
                "speed": StatStage.NORMAL,
                "accuracy": StatStage.NORMAL,
                "evasion": StatStage.NORMAL
            }
    
    @property
    def hp_percentage(self) -> float:
        return (self.hp / self.max_hp) * 100
    
    def is_fainted(self) -> bool:
        return self.hp <= 0

@dataclass
class BattleState:
    # 現在のポケモン
    my_pokemon: PokemonState
    opp_pokemon: PokemonState
    
    # フィールド状態
    weather: Weather = Weather.NONE
    terrain: str = "なし"
    hazards_my_side: List[Hazard] = None
    hazards_opp_side: List[Hazard] = None
    
    # ターン数
    turn_count: int = 0
    
    # 相手の選択傾向
    opponent_tendencies: Dict[str, float] = None
    
    def __post_init__(self):
        if self.hazards_my_side is None:
            self.hazards_my_side = []
        if self.hazards_opp_side is None:
            self.hazards_opp_side = []
        if self.opponent_tendencies is None:
            self.opponent_tendencies = {}
    
    def update_from_json(self, turn_data: Dict):
        """JSONデータから状態を更新"""
        self.turn_count = turn_data.get("turn", self.turn_count)
        
        # ポケモン状態の更新
        self.my_pokemon.name = turn_data.get("my_pokemon", self.my_pokemon.name)
        self.my_pokemon.hp = turn_data.get("my_hp", self.my_pokemon.hp)
        
        self.opp_pokemon.name = turn_data.get("opp_pokemon", self.opp_pokemon.name)
        self.opp_pokemon.hp = turn_data.get("opp_hp", self.opp_pokemon.hp)
        
        # アクションから状態を更新
        for action in turn_data.get("actions", []):
            self._process_action(action)
    
    def _process_action(self, action: Dict):
        """アクションを処理して状態を更新"""
        actor = action.get("actor")
        move = action.get("move")
        ability = action.get("ability")
        action_type = action.get("action")
        
        if move:
            self._process_move(actor, move)
        elif ability:
            self._process_ability(actor, ability)
        elif action_type:
            self._process_special_action(actor, action_type, action.get("target"))
    
    def _process_move(self, actor: str, move: str):
        """技の効果を処理"""
        # フィールド技の処理
        field_moves = {
            "ステルスロック": (lambda: self.hazards_opp_side.append(Hazard.STEALTH_ROCK)),
            "まきびし": (lambda: self.hazards_opp_side.append(Hazard.SPIKES)),
            "どくびし": (lambda: self.hazards_opp_side.append(Hazard.TOXIC_SPIKES)),
            "ねばねばネット": (lambda: self.hazards_opp_side.append(Hazard.STICKY_WEB)),
            "にほんばれ": (lambda: setattr(self, 'weather', Weather.SUNNY)),
            "あまごい": (lambda: setattr(self, 'weather', Weather.RAIN)),
            "すなあらし": (lambda: setattr(self, 'weather', Weather.SANDSTORM)),
            "あられ": (lambda: setattr(self, 'weather', Weather.HAIL)),
            "エレキフィールド": (lambda: setattr(self, 'terrain', "エレキフィールド")),
            "サイコフィールド": (lambda: setattr(self, 'terrain', "サイコフィールド")),
            "グラスフィールド": (lambda: setattr(self, 'terrain', "グラスフィールド")),
            "ミストフィールド": (lambda: setattr(self, 'terrain', "ミストフィールド")),
        }
        
        if move in field_moves:
            field_moves[move]()
        
        # 能力変化技の処理
        stat_changing_moves = {
            "つるぎのまい": ("attack", StatStage.SHARPLY_RISEN),
            "ロックカット": ("speed", StatStage.SHARPLY_RISEN),
            "とつげき": ("attack", StatStage.RISEN),
        }
        
        if move in stat_changing_moves:
            stat, change = stat_changing_moves[move]
            target = self.my_pokemon if actor == "me" else self.opp_pokemon
            target.stat_stages[stat] = change
    
    def _process_ability(self, actor: str, ability: str):
        """特性の発動を処理"""
        pokemon = self.my_pokemon if actor == "me" else self.opp_pokemon
        pokemon.ability = ability
        
        # 特性によるフィールド変化
        ability_effects = {
            "かそく": (lambda: self._increase_stat(pokemon, "speed", StatStage.RISEN)),
            "ひひいろのこどう": (lambda: setattr(self, 'weather', Weather.SUNNY)),
            "ハドロンエンジン": (lambda: setattr(self, 'terrain', "エレキフィールド")),
        }
        
        if ability in ability_effects:
            ability_effects[ability]()
    
    def _process_special_action(self, actor: str, action_type: str, target: str = None):
        """特殊アクションを処理"""
        if action_type == "fainted" and target:
            # ポケモンがひんし状態に
            pokemon = self.my_pokemon if target == self.my_pokemon.name else self.opp_pokemon
            pokemon.hp = 0
    
    def _increase_stat(self, pokemon: PokemonState, stat: str, change: StatStage):
        """能力ランクを上昇"""
        current_stage = pokemon.stat_stages[stat]
        new_value = current_stage.value + change.value
        # -6から+6の範囲に制限
        new_value = max(-6, min(6, new_value))
        pokemon.stat_stages[stat] = StatStage(new_value)
    
    def get_state_summary(self) -> Dict:
        """状態のサマリーを取得"""
        return {
            "turn": self.turn_count,
            "my_pokemon": {
                "name": self.my_pokemon.name,
                "hp": self.my_pokemon.hp,
                "ability": self.my_pokemon.ability,
                "stat_stages": {k: v.value for k, v in self.my_pokemon.stat_stages.items()}
            },
            "opp_pokemon": {
                "name": self.opp_pokemon.name,
                "hp": self.opp_pokemon.hp,
                "ability": self.opp_pokemon.ability,
                "stat_stages": {k: v.value for k, v in self.opp_pokemon.stat_stages.items()}
            },
            "field": {
                "weather": self.weather.value,
                "terrain": self.terrain,
                "hazards_my_side": [h.value for h in self.hazards_my_side],
                "hazards_opp_side": [h.value for h in self.hazards_opp_side]
            },
            "opponent_tendencies": self.opponent_tendencies
        }

def load_json_file(json_file_path: str) -> List[Dict]:
    """JSONファイルを読み込む"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {json_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"エラー: JSONの解析に失敗しました: {json_file_path}")
        return []

def create_battle_state_from_json_file(json_file_path: str) -> Optional[BattleState]:
    """JSONファイルからBattleStateを作成"""
    json_data = load_json_file(json_file_path)
    if not json_data:
        return None
    
    first_turn = json_data[0]
    
    # 初期ポケモン状態を作成
    my_pokemon = PokemonState(
        name=first_turn.get("my_pokemon", ""),
        hp=first_turn.get("my_hp", 100)
    )
    
    opp_pokemon = PokemonState(
        name=first_turn.get("opp_pokemon", ""),
        hp=first_turn.get("opp_hp", 100)
    )
    
    # BattleStateを作成
    battle_state = BattleState(
        my_pokemon=my_pokemon,
        opp_pokemon=opp_pokemon,
        turn_count=first_turn.get("turn", 1)
    )
    
    # 全てのターンデータを適用
    for turn_data in json_data:
        battle_state.update_from_json(turn_data)
    
    return battle_state

def find_json_files(directory: str) -> List[str]:
    """指定ディレクトリ内のJSONファイルを検索"""
    json_files = []
    for file in os.listdir(directory):
        if file.endswith('.json') and 'battle' in file.lower():
            json_files.append(os.path.join(directory, file))
    return json_files

# 使用例
def main():
    """メイン実行関数"""
    import sys
    
    # コマンドライン引数からディレクトリを取得、またはデフォルトを使用
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # デフォルトディレクトリ（現在のディレクトリ）
        directory = "."
    
    # ディレクトリの存在確認
    if not os.path.exists(directory):
        print(f"エラー: ディレクトリが見つかりません: {directory}")
        return
    
    # JSONファイルを検索
    json_files = find_json_files(directory)
    
    if not json_files:
        print(f"バトルJSONファイルが見つかりません: {directory}")
        return
    
    print(f"見つかったJSONファイル: {len(json_files)}件")
    
    # 各JSONファイルを処理
    for json_file in json_files:
        print(f"\n処理中: {os.path.basename(json_file)}")
        
        # BattleStateを作成
        battle_state = create_battle_state_from_json_file(json_file)
        
        if battle_state:
            # 状態を表示
            summary = battle_state.get_state_summary()
            print("バトル状態サマリー:")
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            
            # サマリーファイルとして保存（オプション）
            summary_file = json_file.replace('.json', '_summary.json')
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"サマリーを保存: {os.path.basename(summary_file)}")
        else:
            print("バトル状態の作成に失敗しました")

# 個別ファイル処理用の関数
def process_specific_json_file(json_file_path: str):
    """特定のJSONファイルを処理"""
    if not os.path.exists(json_file_path):
        print(f"エラー: ファイルが見つかりません: {json_file_path}")
        return
    
    print(f"処理中: {os.path.basename(json_file_path)}")
    
    # BattleStateを作成
    battle_state = create_battle_state_from_json_file(json_file_path)
    
    if battle_state:
        # 状態を表示
        summary = battle_state.get_state_summary()
        print("バトル状態サマリー:")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return battle_state
    else:
        print("バトル状態の作成に失敗しました")
        return None

if __name__ == "__main__":
    # 使用方法1: ディレクトリを指定して実行
    # python battle_state.py /path/to/json/directory
    
    # 使用方法2: 特定のファイルを処理
    battle_state = process_specific_json_file(r"C:\pokemon-ai-tool\.traindata\jpn_pokemon-ground-truth\parsed_results_battle.json")
    
    # デフォルト実行（現在のディレクトリを検索）
    # main()