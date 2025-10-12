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

class PokemonNameCorrector(NameCorrector):
    def __init__(self, pokemon_master_path):
        super().__init__(pokemon_master_path, 'name_ja')

class AbilityNameCorrector(NameCorrector):
    def __init__(self, ability_master_path):
        super().__init__(ability_master_path, 'name_ja')
