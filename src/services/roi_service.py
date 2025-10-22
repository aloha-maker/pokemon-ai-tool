# src/services/roi_service.py
import os
import json
from typing import Dict, Any

class RoiService:
    """ROI設定の読み書きに関するビジネスロジックを担当する"""

    def __init__(self, config_path: str = 'instance/roi_config.json'):
        self.config_path = config_path
        self.default_config = {
            "reference_resolution": {"width": 1280, "height": 720},
            "my_pokemon_name": [0,0,0,0],
            "opponent_pokemon_name": [0,0,0,0],
            "my_pokemon_hp": [0,0,0,0],
            "opponent_pokemon_hp": [0,0,0,0]
        }

    def get_config(self) -> Dict[str, Any]:
        """ROI設定をファイルから読み込む。ファイルがなければデフォルト設定を返す。"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.default_config
        except (IOError, json.JSONDecodeError) as e:
            # ファイル読み込みやJSONパースでエラーが起きた場合はエラーを伝播させる
            raise RuntimeError(f"Failed to read or parse ROI config: {e}") from e

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """新しいROI設定をファイルに書き込む。"""
        if not isinstance(new_config, dict):
            raise TypeError("Configuration data must be a dictionary.")

        try:
            # instance フォルダがなければ作成
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Failed to write ROI config: {e}") from e

    def get_editor_image_path(self) -> Dict[str, str]:
        """ROIエディタ用の画像パスを返す。"""
        # TODO: このパスは動的に決定する必要がある。
        # リアルタイム解析中の最新フレームや、ユーザーがアップロードした画像など。
        # 現状はハードコードされた値を返す。
        return {"image_path": "/tests/img/battle_basic.png"}
