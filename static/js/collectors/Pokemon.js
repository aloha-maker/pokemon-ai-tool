// Pokemon.js - Pokemonデータ構造を生成する
import { createMove } from './Move.js';

/**
 * UIから収集した生データをもとに、PokemonのJSONオブジェクトを生成する
 * @param {object} rawData - UIから収集したポケモンの生データ
 * @param {string} rawData.name - ポケモン名
 * @param {string} rawData.ability - 特性
 * @param {string} rawData.tera_type - テラスタイプ
 * @param {string} rawData.item - 持ち物
 * @param {string[]} rawData.moves - 技名の配列
 * @param {number} rawData.hpPercentage - 現在のHP率
 * @returns {object} - 構造化されたPokemonオブジェクト
 */
export function createPokemon(rawData) {
    const {
        name,
        ability,
        tera_type,
        item,
        moves: moveNames, // movesは技名の配列を期待
        hpPercentage
    } = rawData;

    // --- UIに存在しない項目（仮データ） ---
    const level = 50;
    const iv = { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 };
    const ev = { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 };
    const nature = "まじめ";

    // Moveオブジェクトのリストを生成
    const moves = moveNames ? moveNames.map(moveName => createMove(moveName)) : [];

    // --- JSONオブジェクトの構築 ---
    const pokemonJson = {
        name: name || null,
        level: level,
        iv: iv,
        ev: ev,
        nature: nature,
        ability: ability || null,
        item: item || null,
        tera_type: tera_type || null,
        moves: moves,
        current_hp_percentage: hpPercentage || 100,
        base_stats: null,
        types: null,
        status: null,
        boosts: { atk: 0, def: 0, spa: 0, spd: 0, spe: 0 }
    };

    return pokemonJson;
}
