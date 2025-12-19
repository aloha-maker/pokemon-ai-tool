import json
import re
from itertools import groupby
from typing import List,Optional
from src.schemas.pokemon_battle import BattleState
from src.services.calculate_service import DamageCalculator
from src.core.ocr.name_corrector import LiveTextCorrector
from src.core.ocr import config

class BattleStateUpdater:
    """
    ROI名＋OCRテキストを解析して BattleState を更新する
    - 同一frame_idxのイベントをまとめて処理
    - フレーム処理後にmy_pokemon_nameが含まれていた場合にターン更新＆シミュレーション実行
    """

    # def __init__(self, battle_state: BattleState, calculator: DamageCalculator):
    def __init__(self, battle_state: BattleState):
        self.state = battle_state
        # self.calculator = calculator
        self.frame_count = 0
        self.weather_rules = self._load_weather_rules()
        self.live_text_corrector = LiveTextCorrector(live_text_master_path=config.LIVE_TEXT_MASTER_PATH)

    # =====================================================
    # --- フレーム単位処理 ---
    # =====================================================

    def apply_frames(self, events: List):
        """RawBattleEventModel のリストを frame_idx 単位で適用"""
        # frame_idx順にソート → グループ化
        events = sorted(events, key=lambda e: e.sequence)

        for frame_idx, frame_events in groupby(events, key=lambda e: e.sequence):
            frame_events = list(frame_events)
            self.frame_count += 1
            print(f"\n=== Frame {frame_idx} ({self.frame_count}枚目) ===")

            # 同一 frame_idx 内のROI群をまとめて処理
            self.apply_frame(frame_events)

    def apply_frame(self, frame_events: List):
        """同一 frame_idx 内のROI群をまとめて処理"""
        has_my_pokemon_name = False

        # --- まず全ROIを反映 ---
        roi_dict = {}
        for ev in frame_events:
            roi_name = (ev.roi_name or "").strip().lower()
            ocr_text = (ev.ocr_text or "").strip()
            roi_dict[roi_name] = ocr_text

            if roi_name == "my_pokemon_name":
                has_my_pokemon_name = True

        # === 特定の組み合わせを結合 ===
        def combine_rows(base_name):
            row1 = roi_dict.pop(f"{base_name}_row1", "")
            row2 = roi_dict.pop(f"{base_name}_row2", "")
            combined = (row1 + row2).strip()
            if combined:
                if base_name  == "live_comment":
                    combined,_ = self.live_text_corrector.find_closest_name(combined)
                roi_dict[base_name] = combined

        combine_rows("live_comment")
        combine_rows("your_tokusei")
        combine_rows("my_tokusei")


        # --- 各ROIを処理 ---
        for roi_name, text in roi_dict.items():
            self.apply_event(roi_name, text)

        # --- すべてのROIを反映し終えてからターン更新＆シミュレーション ---
        if has_my_pokemon_name:
            self._handle_turn_transition()

        # 状態出力
        # self._print_summary()
        return self.state

    # =====================================================
    # --- ターン切り替え時処理 ---
    # =====================================================

    def _handle_turn_transition(self):
        """ターンを更新し、必要であればシミュレーション実行"""
        self.state.field.turn += 1
        print(f"\n[ターン更新] {self.state.field.turn} ターン目開始")
        # print("[シミュレーション] チームダメージ計算を実行中...")
        # results = self.calculator.simulate_team_damage(self.state)
        # print(results)


    # =====================================================
    # --- イベント単位処理 ---
    # =====================================================

    def apply_event(self, roi_name: str, text: str):
        """各ROIのOCRテキストを解析して BattleState に反映"""
        
        if roi_name == "my_pokemon_name":
            self._active_pokemon(side="my", text=text)
        elif roi_name == "opponent_pokemon_name":
            self._active_pokemon(side="opponent", text=text)
        elif roi_name == "my_pokemon_hp":
            self._update_hp(side="my", text=text)
        elif roi_name == "opponent_pokemon_hp":
            self._update_hp(side="opponent", text=text)
        elif roi_name == "win_lose":
            self._update_win_lose(text)
        elif roi_name == "live_comment":
            self._parse_general_text(text)
        # else:
        #     print(f"[未分類] {roi_name}: {text}")

    # =====================================================
    # --- ROIごとの更新処理 ---
    # =====================================================
    def _active_pokemon(self, side: str, text: str):
        """
        場に出ているポケモンをactiveに設定する
        """
        target_side = self.state.side1 if side == "my" else self.state.side2
        members = target_side.team.members
        target_side.active = next((p for p in members if p.name == text), None)


    def _update_hp(self, side: str, text: str):
        """
        HPバーOCR（パーセンテージ小数対応）＋EV推定呼び出し
        """
        target_side = self.state.side1 if side == "my" else self.state.side2
        active = target_side.active

        if active is None:
            return

        # --- HP数値変換 ---
        try:
            percent_value = float(text.strip())
        except ValueError:
            print(f"[HP] {target_side.team_name} {active.name}: 無効なHP値 ({text})")
            return

        percent_value = max(0.0, min(percent_value, 100.0))
        max_hp = active.max_hp or active.calculate_hp()

        prev_hp = getattr(active, "current_hp", max_hp)
        current_hp = int(round(max_hp * (percent_value / 100.0)))

        # --- 更新 ---
        active.max_hp = max_hp
        active.current_hp = current_hp

        print(f"[HP] {target_side.team_name} {active.name}: 約 {current_hp}/{max_hp} ({percent_value:.2f}%)")

        # --- ダメージ差分を算出 ---
        damage = max(0, prev_hp - current_hp)
        # if damage > 0:
        #     print(f"[ダメージ検出] {target_side.team_name} {active.name} が {damage} ダメージを受けた")

        #     # --- 直前の技情報が存在すればEV推定 ---
        #     field = self.state.field
        #     if (
        #         self.calculator
        #         and hasattr(self.calculator, "estimate_ev_from_damage")
        #         and getattr(field, "last_move_name", None)
        #     ):
        #         # 技オブジェクトを取得
        #         move = None
        #         # 攻撃側を決定
        #         atk_side = self.state.side1 if field.last_move_side == "自分" else self.state.side2
        #         attacker = atk_side.active
        #         for m in attacker.moves:
        #             if m.name == field.last_move_name:
        #                 move = m
        #                 break

        #         if move:
        #             print(f"[EV推定] {field.last_move_user} の {field.last_move_name} による被ダメージから推定中...")
        #             try:
        #                 result = self.calculator.estimate_ev_from_damage(
        #                     move=move,
        #                     battle_state=self.state,
        #                     observed_damage=(damage, damage),
        #                     target="defender" if side == "my" else "attacker"
        #                 )
        #                 if result:
        #                     print(f"[EV推定結果] {target_side.team_name} {active.name}: {result.estimated_ev}")
        #                 else:
        #                     print("[EV推定] 該当候補なし")
        #             except Exception as e:
        #                 print(f"[EV推定エラー] {e}")

    def _update_win_lose(self, text: str):
        if "WIN" in text.upper():
            print("[結果] 自分の勝利！")
        elif "LOSE" in text.upper():
            print("[結果] 自分の敗北…")
        else:
            print("[結果] 判定中…")

    def _load_weather_rules(self):
        """JSONからテキスト→天候ルールを読み込む"""
        with open(config.LIVE_TEXT_MASTER_PATH, encoding="utf-8") as f:
            data = json.load(f)

        # live_text をキーにした辞書を作る
        return {
            item["live_text"]: item
            for item in data["live_text"]
        }

    # =========================
    # --- OCRテキスト解析 ---
    # =========================
    def _parse_general_text(self, text: str):
        """
        ROIに依存しないバトルテキストを解析
        （天候・技発動・交代・特性など）
        """

        # --- 天候・フィールド・場の状態変化 ---
        rule = self.weather_rules.get(text)
        if rule:
            # 天候とフィールドの処理
            if rule["category"] == "wether":
                self.state.field.weather = rule["description"] if rule["switch"] == "on" else None
            elif rule["category"] == "terrain":
                self.state.field.terrain = rule["description"] if rule["switch"] == "on" else None

            # サイド効果の処理
            elif rule["category"] == "side":
                self._apply_side_effect(rule)

        # --- 技の使用（2パターン対応） ---
        elif match := re.search(r"(相手の)?\s*([^\sは]+?)は\s*(.+?)を\s*(?:つかった)[！!]", text):
            self._handle_move_usage(match)
        elif match := re.search(r"(相手の)?\s*([^\sの]+?)の\s*([^\s！!]+)[！!]", text):
            self._handle_move_usage(match)

        # --- 交代・登場（例：「〇〇をくりだした！」） ---
        elif match := re.search(r"(?:\S+?は)?\s*([^\sを]+?)を\s*くりだした", text):
            name = match.group(1).strip()
            # 相手側の交代
            target_side = self.state.side2
            side_label = "相手"
            self._switch_active_pokemon(target_side, name)
            print(f"[交代] {side_label}側が {name} をくりだした")

        # --- 交代（例：「ゆけっ！〇〇！」 or 「がんばれ！〇〇！」） ---
        elif match := re.search(r"(?:ゆけっ|がんばれ)[！!]\s*([^\s！!]+)", text):         
            name = match.group(1).strip()
            target_side = self.state.side1
            side_label = "自分"
            self._switch_active_pokemon(target_side, name)
            print(f"[交代] {side_label}側が {name} をくりだした")

        # --- ポケモンが倒れた（瀕死） ---
        elif match := re.search(r"(相手の)?\s*([^\sは]+)はたおれた", text):
            is_opponent = bool(match.group(1))
            name = match.group(2).strip()

            if is_opponent:
                target_side = self.state.side2
                side_label = "相手"
            else:
                target_side = self.state.side1
                side_label = "自分"

            # 対象ポケモンを検索
            pokemon = next((p for p in target_side.team if p.name == name), None)
            if pokemon:
                pokemon.current_hp = 0
                print(f"[瀕死] {side_label}側の {name} が倒れた！（HP=0）")

            else:
                print(f"[警告] {side_label}側に {name} が見つかりません")

        # --- その他未分類 ---
        # else:
        #     # 任意でデバッグ表示
        #     print(f"[未分類交代検出?] {text}")
                
    def _apply_side_effect(self, rule):
        """サイド効果(スクリーン、設置技など)を適用する"""
        # サイドの選択
        side = self.state.side1 if rule["side"] == "my" else self.state.side2
        
        # 効果のオン/オフ
        is_active = rule["switch"] == "on"
        
        # スクリーン系
        if rule["description"] in ("reflect", "light_screen", "aurora_veil"):
            side.screens[rule["description"]] = is_active
        # 設置技系
        elif rule["description"] in ("stealth_rock", "tailwind"):
            print('ステルスロック')
            side.side_conditions[rule["description"]] = is_active
        
        elif rule["description"] in ("spikes", "toxic_spikes"):
            if is_active:
                side.side_conditions[rule["description"]] += 1
            else:
                side.side_conditions[rule["description"]] = 0

    def _switch_active_pokemon(self, side, name: str):
        """指定サイドのアクティブポケモンを交代"""
        pokemon = next((p for p in side.team if p.name == name), None)
        if pokemon:
            side.set_active(pokemon)
        else:
            print(f"[警告] {side.team_name} に {name} が見つかりません")

    def _handle_move_usage(self, match: re.Match, pattern_type: str = "no"):
        """
        技使用イベントを処理する共通関数。
        pattern_type: "no"（～の～！形式） or "ha"（～は～をつかった！形式）
        """
        if pattern_type == "no":
            is_opponent = bool(match.group(1))
            user_name = match.group(2).strip()
            move_name = match.group(3).strip()
        elif pattern_type == "ha":
            is_opponent = bool(match.group(1))
            user_name = match.group(2).strip()
            move_name = match.group(3).strip()
        else:
            return  # 想定外のパターン

        # --- サイド判定 ---
        target_side = self.state.side2 if is_opponent else self.state.side1
        side_label = "相手" if is_opponent else "自分"

        # --- ポケモン検索 ---
        user_pokemon = next((p for p in target_side.team if p.name == user_name), None)
        if not user_pokemon:
            print(f"[警告] {side_label}側に {user_name} が見つかりません（技使用解析）")

        # --- ログ出力 ---
        print(f"[技] {side_label}側 {user_name} が {move_name} を使用")

        # --- 状態記録 ---
        self.state.field.last_move_user = user_name
        self.state.field.last_move_name = move_name
        self.state.field.last_move_side = side_label

        # --- 攻撃側の切り替え（任意） ---
        self.state.set_attacker(target_side)


    # =========================
    # --- 状態概要出力 ---
    # =========================
    # def _print_summary(self):
    #     s1 = self.state.side1.active
    #     s2 = self.state.side2.active
    #     t = self.state.field.turn

    #     name1 = s1.name if s1 else "（交代待ち）"
    #     name2 = s2.name if s2 else "（交代待ち）"

    #     hp1 = f"{s1.current_hp}/{s1.max_hp}" if s1 else "--/--"
    #     hp2 = f"{s2.current_hp}/{s2.max_hp}" if s2 else "--/--"

    #     print(f"[状態] {t}T | {self.state.side1.team_name}: {name1}({hp1}) vs {self.state.side2.team_name}: {name2}({hp2})")
