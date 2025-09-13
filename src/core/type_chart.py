# type_chart.py

# タイプ相性表データ
# キー: 攻撃側のタイプ, 値: {防御側タイプ: 倍率} の辞書
TYPE_EFFECTIVENESS = {
    'ノーマル': {'いわ': 0.5, 'はがね': 0.5, 'ゴースト': 0},
    'ほのお': {'くさ': 2, 'こおり': 2, 'むし': 2, 'はがね': 2, 'ほのお': 0.5, 'みず': 0.5, 'いわ': 0.5, 'ドラゴン': 0.5},
    'みず': {'ほのお': 2, 'じめん': 2, 'いわ': 2, 'みず': 0.5, 'くさ': 0.5, 'ドラゴン': 0.5},
    'でんき': {'みず': 2, 'ひこう': 2, 'でんき': 0.5, 'くさ': 0.5, 'ドラゴン': 0.5, 'じめん': 0},
    'くさ': {'みず': 2, 'じめん': 2, 'いわ': 2, 'ほのお': 0.5, 'くさ': 0.5, 'どく': 0.5, 'ひこう': 0.5, 'むし': 0.5, 'ドラゴン': 0.5, 'はがね': 0.5},
    # ... 他の全18タイプの相性をここに追加 ...
    'フェアリー': {'かくとう': 2, 'ドラゴン': 2, 'あく': 2, 'ほのお': 0.5, 'どく': 0.5, 'はがね': 0.5}
}

def get_effectiveness(attack_type, defense_types):
    """
    技のタイプ相性倍率を計算する関数
    Args:
        attack_type (str): 攻撃技のタイプ
        defense_types (list[str]): 防御側ポケモンのタイプ（1つまたは2つ）
    Returns:
        float: ダメージ倍率
    """
    if not attack_type:
        return 1.0

    total_effectiveness = 1.0
    if attack_type in TYPE_EFFECTIVENESS:
        for def_type in defense_types:
            if def_type: # タイプ2が存在しない場合を考慮
                total_effectiveness *= TYPE_EFFECTIVENESS[attack_type].get(def_type, 1.0)
    
    return total_effectiveness
