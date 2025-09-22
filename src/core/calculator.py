# src/core/calculator.py

import math

def calculate_status(base_stats, level, evs, ivs, nature):
    """
    ポケモンのステータス実数値を計算する。

    Args:
        base_stats (dict): 種族値 (hp, attack, defense, sp_attack, sp_defense, speed)
        level (int): レベル
        evs (dict): 努力値 (hp, attack, defense, sp_attack, sp_defense, speed)
        ivs (dict): 個体値 (hp, attack, defense, sp_attack, sp_defense, speed)
        nature (dict): 性格補正 (increased_stat, decreased_stat)

    Returns:
        dict: 計算された各ステータスの実数値
    """
    stats = {}

    # HPの計算
    stats['hp'] = math.floor(((base_stats['hp'] * 2 + ivs['hp'] + math.floor(evs['hp'] / 4)) * level) / 100) + level + 10

    # HP以外のステータス計算
    for stat_name in ['attack', 'defense', 'sp_attack', 'sp_defense', 'speed']:
        base_val = base_stats[stat_name]
        iv_val = ivs[stat_name]
        ev_val = evs[stat_name]
        
        # 基本計算
        main_stat = math.floor(((base_val * 2 + iv_val + math.floor(ev_val / 4)) * level) / 100) + 5
        
        # 性格補正
        nature_multiplier = 1.0
        if nature and nature.get('increased_stat') == stat_name:
            nature_multiplier = 1.1
        elif nature and nature.get('decreased_stat') == stat_name:
            nature_multiplier = 0.9
            
        stats[stat_name] = math.floor(main_stat * nature_multiplier)
        
    return stats

def calculate_damage():
    # TODO: ダメージ計算ロジックを実装
    pass
