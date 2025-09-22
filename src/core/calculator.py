# src/core/calculator.py

import math

from src.core import type_chart

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

def calculate_damage(attacker_level, move_power, attack_stat, defense_stat, move_type, defender_type1, defender_type2=None):
    """
    基本的なダメージ計算を行う。

    Args:
        attacker_level (int): 攻撃側のレベル
        move_power (int): 技の威力
        attack_stat (int): 攻撃側の能力値（物理なら攻撃、特殊なら特攻）
        defense_stat (int): 防御側の能力値（物理なら防御、特殊なら特防）
        move_type (str): 技のタイプ
        defender_type1 (str): 防御側のタイプ1
        defender_type2 (str, optional): 防御側のタイプ2

    Returns:
        tuple: (最小ダメージ, 最大ダメージ)
    """
    if move_power == 0:
        return (0, 0)

    # 基本ダメージ計算
    base_damage = math.floor(math.floor(math.floor(attacker_level * 2 / 5) + 2) * move_power * attack_stat / defense_stat)
    base_damage = math.floor(base_damage / 50) + 2

    # タイプ相性
    effectiveness = type_chart.get_effectiveness(move_type.lower(), [t.lower() for t in [defender_type1, defender_type2] if t])
    
    # 乱数以外の補正は一旦1.0とする
    # TODO: 天候、持ち物、特性などの補正を追加
    modifiers = effectiveness

    # 16段階のダメージ計算 (乱数 0.85 ~ 1.0)
    min_damage = math.floor(base_damage * modifiers * 0.85)
    max_damage = math.floor(base_damage * modifiers * 1.0)

    return (min_damage, max_damage)
