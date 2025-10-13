# name_corrector.py
import os
import pandas as pd

class NameCorrector:
    def __init__(self, master_path, column_name):
        self.names = self._load_names(master_path, column_name)

    def _load_names(self, path, column_name):
        if not os.path.exists(path):
            print(f"警告: マスターファイル '{path}' が見つかりません。名前補正は無効になります。")
            return []
        try:
            df = pd.read_csv(path)
            return [name for name in df[column_name].unique() if pd.notna(name)]
        except Exception as e:
            print(f"警告: マスターファイル '{path}' の読み込み中にエラーが発生しました: {e}")
            return []

    def find_closest_name(self, text, threshold=2):
        if not self.names or not text:
            return text
        if text in self.names:
            return text
        closest_name = min(self.names, key=lambda name: self._levenshtein_distance(text, name))
        min_distance = self._levenshtein_distance(text, closest_name)
        return closest_name if min_distance <= threshold else text

    def _levenshtein_distance(self, s1, s2):
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def find_closest_name_in_list(self, text, candidate_list):
        """
        候補リストから最も近い名前を検索
        """
        if not text or not candidate_list:
            return text
        
        # 完全一致チェック
        if text in candidate_list:
            return text
        
        # 類似度ベースで検索
        best_match = text
        best_similarity = 0
        
        for candidate in candidate_list:
            similarity = self.calculate_similarity(text, candidate)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate
        
        print(f"  📊 候補リストから検索: '{text}' → '{best_match}' (類似度: {best_similarity:.2f})")
        return best_match

    def calculate_similarity(self, text1, text2):
        """
        2つの文字列の類似度を計算（0.0〜1.0）
        既存の類似度計算メソッドがあればそれを使用
        """
        # 既存の類似度計算ロジックを使用
        # もし別のメソッド名で実装されている場合は適宜変更
        if hasattr(self, '_calculate_similarity'):
            return self._calculate_similarity(text1, text2)
        else:
            # 簡易的な類似度計算（レーベンシュタイン距離ベース）
            from difflib import SequenceMatcher
            return SequenceMatcher(None, text1, text2).ratio()

class PokemonNameCorrector(NameCorrector):
    def __init__(self, pokemon_master_path):
        super().__init__(pokemon_master_path, 'name_ja')

class AbilityNameCorrector(NameCorrector):
    def __init__(self, ability_master_path):
        super().__init__(ability_master_path, 'name_ja')
