# phase_manager.py
class PhaseManager:
    def __init__(self):
        self.current_phase = "stay"
        self.battle_sub_phase = "act"
        self.processed_rois = set()
        self.battle_flags = {}
        self.stop_flag = False
        self.return_flag = False
    
    def should_process_roi(self, roi_name):
        """ROIが処理可能かチェック"""
        return roi_name not in self.processed_rois
    
    def mark_processed(self, roi_name):
        """ROIを処理済みとしてマーク"""
        self.processed_rois.add(roi_name)
    
    def reset_battle_flags(self):
        """バトル関連のフラグをリセット"""
        self.battle_flags = {}
        # バトル関連のROI処理フラグもリセット
        battle_rois = [
            'my_pokemon_name', 'my_pokemon_hp', 'my_ailment',
            'opponent_pokemon_name', 'opponent_pokemon_hp', 'your_ailment'
        ]
        for roi_name in battle_rois:
            if roi_name in self.processed_rois:
                self.processed_rois.remove(roi_name)
    
    def set_phase(self, phase, sub_phase=None):
        """フェーズを設定"""
        old_phase = self.current_phase
        self.current_phase = phase
        self.battle_sub_phase = sub_phase
        
        # フェーズ変更時に処理済みROIをクリア
        if phase == "stay":
            self.processed_rois.clear()
        elif old_phase != phase and phase == "battle":
            # バトル開始時にバトルフラグをリセット
            self.reset_battle_flags()
    
    def get_current_phase(self):
        """現在のフェーズを取得"""
        return {
            "current_phase": self.current_phase,
            "battle_sub_phase": self.battle_sub_phase if self.current_phase == "battle" else None
        }
    
    def __str__(self):
        phase_info = f"Phase: {self.current_phase}"
        if self.current_phase == "battle":
            phase_info += f".{self.battle_sub_phase}"
        return phase_info
    
    # 互換性のためのメソッド
    def get_current_phase_info(self):
        """現在のフェーズ情報を取得（互換性用）"""
        return self.get_current_phase()