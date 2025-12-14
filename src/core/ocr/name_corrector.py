import pandas as pd
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
from src.extensions import db
from src.models import PokemonModel,AbilityModel
from sqlalchemy import func

class NameCorrector:
    DEFAULT_THRESHOLD = 0.6
    
    def __init__(
        self,
        master_file_path: Optional[str] = None,
        name_column: Optional[str] = None,
        name_list: Optional[List[str]] = None,
        name_dict_list: Optional[List[Dict[str, str]]] = None
    ):
        """
        master_file_path（CSV/Excel）または name_list（配列）のどちらかで初期化可能
        
        Args:
            master_file_path: マスタファイルのパス
            name_column: マスタファイル内の名前カラム
            name_list: 名前のリスト（直接指定する場合）
            name_dict_list: 入力名と正規化名の対応辞書リスト
        """
        self.master_file_path = master_file_path
        self.name_column = name_column
        self.name_dict_list: List[Dict[str, str]] = name_dict_list if name_dict_list is not None else []

        if name_list is not None:
            self.name_list = name_list
        elif master_file_path:
            self.name_list = self._load_name_list()
        else:
            self.name_list = []
    
    def _normalize_from_pokemons_db(self, names: List[str]) -> List[str]:
        """
        DBから正規化された名前と元の入力名の対応辞書リストを取得
        
        エイリアス名（例: サトシゲッコウガ）を正規化名（例: ゲッコウガ）に変換
        base_idが同じポケモンの中で、idが最小のものを正規化名とする
        
        Args:
            names: 入力名のリスト（エイリアス含む）
            
        Returns:
            入力名と正規化名の対応辞書リスト
            [{"input_name": "サトシゲッコウガ", "normalized_name": "ゲッコウガ"}, ...]
        """
        try:
            # 1. origin CTE
            origin = (
                db.session.query(
                    PokemonModel.base_id.label("base_id"),
                    PokemonModel.name_ja.label("input_name")
                )
                .filter(PokemonModel.name_ja.in_(names))
                .cte("origin")
            )

            # 2. base_idごとの正規化名（id最小）
            normalized = (
                db.session.query(
                    PokemonModel.base_id.label("base_id"),
                    func.min(PokemonModel.id).label("min_id")
                )
                .group_by(PokemonModel.base_id)
                .subquery()
            )

            # 3. origin × 正規化名 JOIN
            results = (
                db.session.query(
                    PokemonModel.name_ja.label("normalized_name"),
                    origin.c.input_name
                )
                .join(normalized, normalized.c.min_id == PokemonModel.id)
                .join(origin, origin.c.base_id == PokemonModel.base_id)
                .all()
            )

            return [
                {
                    "input_name": r.input_name,
                    "normalized_name": r.normalized_name
                }
                for r in results
            ]

        except Exception as e:
            print(f"DB正規化エラー: {e}")
            return []
    
    def _normalize_from_abilities_db(self, poke_names: List[str]) -> List[str]:
        """
        指定ポケモンが持つ全特性の名前リストを取得
        
        Args:
            poke_names: ポケモン名のリスト
            
        Returns:
            特性名のリスト（重複なし）
        """
        try:
            # 1. abilities を取得
            rows = (
                db.session.query(PokemonModel.abilities)
                .filter(PokemonModel.name_ja.in_(poke_names))
                .all()
            )

            # 2. カンマ区切りを分解して数値化
            ability_ids = set()

            for (ability_str,) in rows:
                if ability_str:
                    for p in ability_str.split(","):
                        ability_ids.add(int(p))

            # 3. abilities テーブルから対応するIDを取得
            result_abilities = (
                db.session.query(AbilityModel)
                .filter(AbilityModel.id.in_(ability_ids))
                .all()
            )
            return [r.name_ja for r in result_abilities]
        except Exception as e:
            print(f"DB正規化エラー: {e}")
            return []
    
    def _load_name_list(self):
        """マスタファイルから名前リストを読み込む"""
        try:
            if self.master_file_path.endswith('.csv'):
                df = pd.read_csv(self.master_file_path)
            else:
                df = pd.read_excel(self.master_file_path)
            
            if self.name_column in df.columns:
                return df[self.name_column].dropna().unique().tolist()
            else:
                print(f"⚠ カラム '{self.name_column}' が見つかりません")
                return []
        except Exception as e:
            print(f"マスタファイルの読み込みエラー: {e}")
            return []
        
    def find_closest_name(self, text, threshold=DEFAULT_THRESHOLD):
        """
        最も近い名前を検索（閾値以上のもののみ）
        
        Args:
            text: 検索対象のテキスト
            threshold: 類似度の閾値（デフォルト: 0.6）
            return_dict: Trueの場合、辞書形式で返す（後方互換性のため）
            
        Returns:
            最も近い名前（閾値未満の場合は元のテキスト）
        """        
        # 類似度ベースで検索用
        best_match = text
        best_similarity = 0.0
        best_original_name = text

        # 候補リストを統一的に処理
        candidates = (
            [(item["normalized_name"], item["input_name"]) for item in self.name_dict_list]
            if self.name_dict_list
            else [(name, name) for name in self.name_list]
        )
        print('text',text)
        print('candidates',candidates)

        for normalized, original in candidates:
            # 完全一致チェック
            if normalized == text:
                return original
            
            # 類似度ベースで検索
            similarity = self._simple_similarity(text, normalized)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = normalized
                best_original_name = original
        
        # 閾値チェック
        if best_similarity >= threshold:
            print(f"  📊 検索: '{text}' → '{best_match}' (類似度: {best_similarity:.2f})")
            if self.name_dict_list:
                print(f"  🔄 辞書逆引き: '{best_match}' → '{best_original_name}'")
            return best_original_name
        else:
            print(f"  ⚠ 類似度不足: '{text}' (最良: '{best_match}', 類似度: {best_similarity:.2f} < {threshold})")
            return text
    
    def _simple_similarity(self, text1, text2):
        """
        シンプルな類似度計算（レーベンシュタイン距離ベース）
        
        Args:
            text1: 比較対象1
            text2: 比較対象2
            
        Returns:
            類似度（0.0～1.0）
        """
        return SequenceMatcher(None, text1, text2).ratio()

class PokemonNameCorrector(NameCorrector):
    def __init__(
        self, 
        pokemon_master_path: Optional[str] = None, 
        name_list: Optional[List[str]] = None
    ):
        """
        Args:
            pokemon_master_path: ポケモンマスタファイルのパス
            name_list: ポケモン名のリスト（DBから取得する場合）
        """
        poke_name_list: List[str] = []
        poke_name_dict_list: List[Dict[str, str]] = []

        if name_list is not None:
            # DBから正規化辞書リストを取得
            poke_name_dict_list = self._normalize_from_pokemons_db(name_list)
            # find_closest_name() で使う name_list は、正規化された名前のみ
            poke_name_list = [d["normalized_name"] for d in poke_name_dict_list]

        # CSVか配列のどちらかで初期化できるようにする
        super().__init__(
            master_file_path=pokemon_master_path,
            name_column='name_ja',
            name_list=poke_name_list,
            name_dict_list=poke_name_dict_list
        )

class AbilityNameCorrector(NameCorrector):
    def __init__(
        self, 
        ability_master_path: Optional[str] = None, 
        poke_name_list: Optional[List[str]] = None
    ):
        """
        Args:
            ability_master_path: 特性マスタファイルのパス
            poke_name_list: ポケモン名のリスト（このリストから特性を抽出）
        """
        abilities_name_list: List[str] = []
        if poke_name_list is not None:
            abilities_name_list = self._normalize_from_abilities_db(poke_name_list)

        super().__init__(
            master_file_path=ability_master_path,
            name_column='name_ja',
            name_list=abilities_name_list
        )