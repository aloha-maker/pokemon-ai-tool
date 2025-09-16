import sqlite3
import os
from ..core.type_chart import get_effectiveness

# データベースファイルのパスをプロジェクトルートからの相対パスで解決
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "pokemon_ai.db")


class ActionAIModel:
    """
    ルールベースで行動を予測するAIモデルのプロトタイプ。
    """
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row # カラム名でアクセスできるようにする

    def _get_pokemon_types(self, pokemon_name):
        """ポケモン名からタイプを取得する"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT type1, type2 FROM pokemons WHERE name LIKE ?", (f'%{pokemon_name}%',))
        result = cursor.fetchone()
        if result:
            return [t for t in [result['type1'], result['type2']] if t]
        return []

    def _get_move_type(self, move_name):
        """技名からタイプを取得する"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT type FROM moves WHERE name LIKE ?", (f'%{move_name}%',))
        result = cursor.fetchone()
        return result['type'] if result else None

    def predict_action(self, game_state):
        """
        盤面情報から最適な行動を予測する。

        Args:
            game_state (dict): GameStateParserから得られる盤面情報
                例: {
                    'my_pokemon_name': 'ピカチュウ',
                    'opponent_pokemon_name': 'ゼニガメ',
                    'moves_list': ['10まんボルト', 'でんこうせっか', 'たたきつける', 'かげぶんしん']
                }
        Returns:
            dict: 推奨アクションと理由
        """
        my_poke_name = game_state.get('my_pokemon_name')
        opp_poke_name = game_state.get('opponent_pokemon_name')
        my_moves = game_state.get('moves_list', [])

        if not my_poke_name or not opp_poke_name:
            return {"action": "待機", "reason": "盤面情報が不十分です。"}

        my_types = self._get_pokemon_types(my_poke_name)
        opp_types = self._get_pokemon_types(opp_poke_name)

        if not my_types or not opp_types:
            return {"action": "待機", "reason": "DBからポケモン情報が見つかりません。"}
        
        # --- 攻撃評価 ---
        best_move = None
        max_effectiveness = -1.0

        for move_name in my_moves:
            if not move_name: continue
            move_type = self._get_move_type(move_name)
            effectiveness = get_effectiveness(move_type, opp_types)
            
            if effectiveness > max_effectiveness:
                max_effectiveness = effectiveness
                best_move = move_name
        
        # --- 防御評価 (相手のタイプが自分に抜群か) ---
        is_at_disadvantage = False
        for opp_type in opp_types:
            effectiveness_on_me = get_effectiveness(opp_type, my_types)
            if effectiveness_on_me >= 2.0:
                is_at_disadvantage = True
                break
        
        # --- 総合判断 ---
        if is_at_disadvantage and max_effectiveness < 2.0:
            return {
                "action": "交代",
                "target": "有利なポケモン", # TODO: 控えポケモンとの相性評価を実装
                "reason": f"相手のタイプ({', '.join(opp_types)})がこちらの弱点です。交代を推奨します。"
            }
        
        if max_effectiveness >= 2.0:
             return {
                "action": "技選択",
                "target": best_move,
                "reason": f"技「{best_move}」は相手に効果抜群です (倍率: x{max_effectiveness})。"
            }
        
        return {
            "action": "技選択",
            "target": best_move,
            "reason": f"最もダメージが期待できる技は「{best_move}」です (倍率: x{max_effectiveness})。"
        }
    
    def __del__(self):
        self.conn.close()
