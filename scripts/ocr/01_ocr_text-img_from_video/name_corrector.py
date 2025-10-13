import os
import pandas as pd
from difflib import SequenceMatcher

class NameCorrector:
    def __init__(self, master_file_path, name_column):
        self.master_file_path = master_file_path
        self.name_column = name_column
        self.name_list = self._load_name_list()
    
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
                print(f"警告: カラム '{self.name_column}' がマスタファイルに見つかりません")
                return []
        except Exception as e:
            print(f"マスタファイルの読み込みエラー: {e}")
            return []
        
    def find_closest_name(self, text, threshold=0.6):
        """
        全リストから最も近い名前を検索（類似度0.6以上のみ）
        閾値未満の場合は元のテキストを返す
        """
        if not text or not self.name_list:
            return text
        
        # 完全一致チェック
        if text in self.name_list:
            print(f"  ✅ 完全一致: '{text}' (類似度: 1.0)")
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
        """
        シンプルな類似度計算（レーベンシュタイン距離ベース）
        """
        return SequenceMatcher(None, text1, text2).ratio()

def find_closest_name_with_similarity(self, text, threshold=0.6):
    """
    テスト用: 最も近い名前と類似度を返す（閾値チェックあり）
    """
    if not text or not self.name_list:
        return text, 0.0
    
    # 完全一致チェック
    if text in self.name_list:
        return text, 1.0
    
    # 類似度ベースで検索
    best_match = text
    best_similarity = 0
    
    for candidate in self.name_list:
        similarity = self._simple_similarity(text, candidate)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = candidate
    
    # 閾値チェック
    if best_similarity >= threshold:
        return best_match, best_similarity
    else:
        return text, best_similarity

def find_all_matches(self, text, min_similarity=0.0):
    """
    テスト用: 類似度順に全ての候補を返す
    """
    if not text or not self.name_list:
        return []
    
    matches = []
    for candidate in self.name_list:
        similarity = self._simple_similarity(text, candidate)
        if similarity >= min_similarity:
            matches.append({
                'candidate': candidate,
                'similarity': similarity
            })
    
    # 類似度でソート
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    return matches


class PokemonNameCorrector(NameCorrector):
    def __init__(self, pokemon_master_path):
        super().__init__(pokemon_master_path, 'name_ja')


class AbilityNameCorrector(NameCorrector):
    def __init__(self, ability_master_path):
        super().__init__(ability_master_path, 'name_ja')