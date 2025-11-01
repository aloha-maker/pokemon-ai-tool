import re
from itertools import groupby
from typing import List
from src.schemas.pokemon_battle import BattleState


class BattleStateUpdater:
    """
    ROI名＋OCRテキストを解析して BattleState を更新する
    - 同一frame_idxのイベントは同時に処理
    - roi_config.json に基づき my / opponent の判定やHP更新を行う
    """

    def __init__(self, battle_state: BattleState):
        self.state = battle_state
        self.frame_count = 0

    # =====================================================
    # --- フレーム単位処理 ---
    # =====================================================

    def apply_frames(self, events: List):
        """
        DBから取得した RawBattleEventModel のリストを frame_idx 単位で適用する。
        """
        # frame_idx順にソート → グループ化
        events = sorted(events, key=lambda e: e.sequence)

        for frame_idx, frame_events in groupby(events, key=lambda e: e.sequence):
            frame_events = list(frame_events)
            self.frame_count += 1
            print(f"\n=== Frame {frame_idx} ({self.frame_count}枚目) ===")

            # 同一フレームのROI群をまとめて適用
            self.apply_frame(frame_events)

    def apply_frame(self, frame_events: List):
        """
        同一 frame_idx 内の全ROIをまとめて処理。
        """
        for event in frame_events:
            roi_name = event.roi_name
            ocr_text = event.ocr_text
            self.apply_event(roi_name, ocr_text)

        # フレーム終了後に状態要約を表示（デバッグ用）
        self._print_summary()

    # =====================================================
    # --- イベント単位の解析 ---
    # =====================================================

    def apply_event(self, roi_name: str, ocr_text: str):
        """
        各ROIごとのOCRテキストを解析して BattleState に反映。
        """
        if not ocr_text or not isinstance(ocr_text, str):
            return

        text = ocr_text.strip()
        if not text:
            return

        # --- ROI別の分岐 ---
        if roi_name == "my_pokemon_name":
            # ターン更新をここで実行
            self.state.field.turn += 1
            print(f"\n[ターン更新] {self.state.field.turn} ターン目開始")
            self._update_active_name(side="my", text=text)
        elif roi_name == "opponent_pokemon_name":
            self._update_active_name(side="opponent", text=text)
        elif roi_name == "my_pokemon_hp":
            self._update_hp(side="my", text=text)
        elif roi_name == "opponent_pokemon_hp":
            self._update_hp(side="opponent", text=text)
        elif roi_name == "win_lose":
            self._update_win_lose(text)
        else:
            # その他のROIはテキスト解析ベース
            self._parse_general_text(text)

    # =====================================================
    # --- ROIごとの更新処理 ---
    # =====================================================

    def _update_active_name(self, side: str, text: str):
        """場のポケモン名更新"""
        target_side = self.state.side1 if side == "my" else self.state.side2
        candidate = next((p for p in target_side.team if p.name == text), None)
        if candidate:
            target_side.set_active(candidate)
            print(f"[交代] {target_side.team_name}側が {text} に交代")
        else:
            print(f"[OCR] {target_side.team_name}側に '{text}' の個体は未登録")

    def _update_hp(self, side: str, text: str):
        """HPバー情報の更新 (例: '120/150')"""
        match = re.search(r"(\d+)\s*/\s*(\d+)", text)
        if not match:
            return
        current_hp = int(match.group(1))
        max_hp = int(match.group(2))

        target_side = self.state.side1 if side == "my" else self.state.side2
        active = target_side.active
        active.current_hp = current_hp
        active.max_hp = max_hp
        print(f"[HP] {target_side.team_name} {active.name}: {current_hp}/{max_hp}")

    def _update_win_lose(self, text: str):
        """勝敗の更新"""
        if "WIN" in text.upper():
            print("[結果] 自分の勝利！")
        elif "LOSE" in text.upper():
            print("[結果] 自分の敗北…")
        else:
            print("[結果] 判定中…")

    # =====================================================
    # --- OCR文テキスト解析 ---
    # =====================================================

    def _parse_general_text(self, text: str):
        """ROIに依存しないテキスト内容を解析"""
        # 天候
        if "あめ" in text and "ふりはじめ" in text:
            self.state.field.weather = "rain"
            print("[天候] あめが ふりはじめた")

        elif "ひざし" in text and "つよく" in text:
            self.state.field.weather = "sunny"
            print("[天候] ひざしが つよくなった")

        elif "すなあらし" in text and "ふきはじめ" in text:
            self.state.field.weather = "sandstorm"
            print("[天候] すなあらしが ふきはじめた")

        elif match := re.search(r"(.+)を くりだした", text):
            print(f"[行動] {match.group(1)} をくりだした")

        elif match := re.search(r"(.+)の (.+)！", text):
            print(f"[技] {match.group(1)} が {match.group(2)} を使用")

    # =====================================================
    # --- 出力補助 ---
    # =====================================================

    def _print_summary(self):
        """現在の戦況要約（デバッグ表示）"""
        my = self.state.side1
        opp = self.state.side2
        print(f"  自分側: {my.active.name} ({my.active.current_hp}/{my.active.max_hp})")
        print(f"  相手側: {opp.active.name} ({opp.active.current_hp}/{opp.active.max_hp})")
        if self.state.field.weather:
            print(f"  天候: {self.state.field.weather}")
