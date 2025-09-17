import os
from ..core.type_chart import get_effectiveness
from ..database.manager import DatabaseManager


class ActionAIModel:
    """
    ルールベースで行動を予測するAIモデルのプロトタイプ。
    """
    def __init__(self):
        # DatabaseManagerのインスタンスを保持するが、接続はメソッドごとに行う
        self.db_manager = DatabaseManager()

    def _get_pokemon_types(self, db, pokemon_name):
        """ポケモン名からタイプを取得する"""
        pokemon = db.get_pokemon_by_name(pokemon_name)
        if pokemon:
            return [t for t in [pokemon['type1'], pokemon['type2']] if t]
        return []

    def _get_move_type(self, db, move_name):
        """技名からタイプを取得する"""
        move = db.get_move_by_name(move_name)
        return move['type'] if move else None

    def _parse_hp(self, hp_string: str) -> dict | None:
        """HPの文字列（例: '123/456'）をパースして辞書を返す"""
        if not hp_string or '/' not in hp_string:
            return None
        try:
            parts = hp_string.split('/')
            current = int(parts[0])
            maximum = int(parts[1])
            percentage = (current / maximum) * 100 if maximum > 0 else 0
            return {"current": current, "max": maximum, "percentage": percentage}
        except (ValueError, IndexError):
            return None

    def predict_action(self, game_state):
        """
        盤面情報から最適な行動を予測する。
        """
        my_poke_name = game_state.get('my_pokemon_name')
        opp_poke_name = game_state.get('opponent_pokemon_name')
        my_hp_str = game_state.get('my_pokemon_hp')
        my_moves = game_state.get('moves_list', [])

        if not my_poke_name or not opp_poke_name:
            return {"action": "待機", "reason": "盤面情報が不十分です。"}

        with self.db_manager as db:
            # --- 盤面情報の解析 ---
            my_types = self._get_pokemon_types(db, my_poke_name)
            opp_types = self._get_pokemon_types(db, opp_poke_name)
            my_hp = self._parse_hp(my_hp_str)

            if not my_types or not opp_types:
                return {"action": "待機", "reason": f"DBからポケモン情報({my_poke_name} or {opp_poke_name})が見つかりません。"}
            
            # --- 防御評価 (相手のタイプが自分に抜群か) ---
            is_at_disadvantage = False
            for opp_type in opp_types:
                effectiveness_on_me = get_effectiveness(opp_type, my_types)
                if effectiveness_on_me >= 2.0:
                    is_at_disadvantage = True
                    break

            # --- 緊急交代の判断 (HPが低く、かつ不利対面) ---
            if my_hp and my_hp['percentage'] < 30 and is_at_disadvantage:
                return {
                    "action": "交代",
                    "target": "有利なポケモン", # TODO: 控えポケモンとの相性評価を実装
                    "reason": f"HPが危険水域({my_hp['percentage']:.0f}%)で、相手({opp_poke_name})がタイプ上有利なため、交代を強く推奨します。"
                }

            # --- 攻撃評価 ---
            best_move = None
            max_effectiveness = -1.0

            for move_name in my_moves:
                if not move_name: continue
                move_type = self._get_move_type(db, move_name)
                if not move_type: continue
                effectiveness = get_effectiveness(move_type, opp_types)
                
                if effectiveness > max_effectiveness:
                    max_effectiveness = effectiveness
                    best_move = move_name
            
            # --- 通常の総合判断 ---
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
            
            if not best_move:
                return {"action": "待機", "reason": "有効な攻撃技が見つかりません。"}

            return {
                "action": "技選択",
                "target": best_move,
                "reason": f"最もダメージが期待できる技は「{best_move}」です (倍率: x{max_effectiveness})。"
            }
    
    
