import pandas as pd
from typing import List
from difflib import SequenceMatcher
from src.extensions import db
from src.models.pokemon_model import PokemonModel

class NameCorrector:
    DEFAULT_THRESHOLD = 0.6
    
    def __init__(
        self
        , master_file_path=None
        , name_column=None
        , name_list=None):
        """
        master_file_path（CSV/Excel）または name_list（配列）のどちらかで初期化可能
        """
        self.master_file_path = master_file_path
        self.name_column = name_column

        if name_list is not None:
            self.name_list = name_list
        elif master_file_path:
            self.name_list = self._load_name_list()
        else:
            self.name_list = []
    
    def _normalize_from_db(self, names: List[str]) -> List[str]:
        """DBから正規化された名前リストを取得"""
        try:
            subquery = (
                db.session.query(PokemonModel.base_id)
                .filter(PokemonModel.name_ja.in_(names))
            )
            print('subquery',subquery)

            results = (
                db.session.query(PokemonModel.name_ja)
                .filter(PokemonModel.id.in_(subquery))
                .all()
            )
            print('results',results)
            return [r.name_ja for r in results]
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
        
    def find_closest_name(self, text, threshold=0.6):
        """最も近い名前を検索（閾値0.6以上のみ）"""
        if not text or not self.name_list:
            return text
        
        # 完全一致チェック
        if text in self.name_list:
            return text
        
        # 類似度ベースで検索
        best_match = text
        best_similarity = 0
        
        for candidate in self.name_list:
            similarity = self._simple_similarity(text, candidate)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate
        
        # 閾値チェック（0.6以上のみ適用）
        if best_similarity >= threshold:
            print("self.name_list:",self.name_list)
            print(f"  📊 検索: '{text}' → '{best_match}' (類似度: {best_similarity:.2f})")
            return best_match
        else:
            print(f"  ⚠ 類似度不足: '{text}' → '{best_match}' (類似度: {best_similarity:.2f} < {threshold})")
            return text  # 閾値未満の場合は元のテキストを返す
        
    def find_closest_name_in_list(self, text, candidate_list, threshold=0.6):
        """
        候補リストから最も近い名前を検索（類似度0.6以上のみ）
        閾値未満の場合は元のテキストを返す
        """
        if not text or not candidate_list:
            return text
        
        # 完全一致チェック
        if text in candidate_list:
            print(f"  ✅ 完全一致: '{text}' (類似度: 1.0)")
            return text
        
        # 類似度ベースで検索
        best_match = text
        best_similarity = 0
        
        for candidate in candidate_list:
            similarity = self._simple_similarity(text, candidate)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate
        
        # 閾値チェック（0.6以上のみ適用）
        if best_similarity >= threshold:
            print(f"  📊 候補リストから検索: '{text}' → '{best_match}' (類似度: {best_similarity:.2f})")
            return best_match
        else:
            print(f"  ⚠ 類似度不足: '{text}' → '{best_match}' (類似度: {best_similarity:.2f} < {threshold})")
            return text  # 閾値未満の場合は元のテキストを返す
    
    def _simple_similarity(self, text1, text2):
        """シンプルな類似度計算"""
        return SequenceMatcher(None, text1, text2).ratio()

class PokemonNameCorrector(NameCorrector):
    def __init__(self, pokemon_master_path=None, name_list=None):
        poke_name_list = []
        if name_list is not None:
            poke_name_list = self._normalize_from_db(name_list)
        # CSVか配列のどちらかで初期化できるようにする
        super().__init__(master_file_path=pokemon_master_path, name_column='name_ja', name_list=poke_name_list)


class AbilityNameCorrector(NameCorrector):
    def __init__(self, ability_master_path):
        super().__init__(ability_master_path, 'name_ja')