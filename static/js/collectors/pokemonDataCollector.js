// pokemonDataCollector.js - 画面からポケモンデータを収集し、構造化するモジュール

import { createPokemon } from './Pokemon.js';
import { createParty } from './Party.js';
import { createBattleSide } from './BattleSide.js';

/**
 * 特定のスロットのUIからポケモンの生データを収集する
 * @param {string} partyType 
 * @param {number} slotIndex 
 * @returns {object|null} - ポケモンの生データ or null
 */
function collectRawPokemonData(partyType, slotIndex) {
    const slotSelector = `.pokemon-slot[data-party-type='${partyType}'][data-slot-index='${slotIndex}']`;
    const slotElement = document.querySelector(slotSelector);

    // スロットが存在しない、またはポケモン名が入力されていなければ対象外
    if (!slotElement || !slotElement.querySelector('.pokemon-input').value) {
        return null;
    }

    // 注意: この実装は、モーダルに表示されている情報が対象スロットのものであることを前提としています。
    const modal = document.getElementById('pokemon-details-modal');
    
    const moveNodes = modal.querySelectorAll('.details-move-input');
    const moves = [];
    moveNodes.forEach(input => {
        if (input.value) {
            moves.push(input.value);
        }
    });

    const hpBar = slotElement.querySelector('.hp-bar');

    return {
        name: slotElement.querySelector('.pokemon-input').value,
        ability: modal.querySelector('#details-ability-input').value,
        tera_type: modal.querySelector('#details-tera-type-select').value,
        item: modal.querySelector('#details-item-input').value,
        moves: moves,
        hpPercentage: hpBar ? parseFloat(hpBar.style.width) : 100
    };
}

/**
 * 特定のスロットのポケモンデータを収集し、構造化されたJSONを返す
 * @param {string} partyType 
 * @param {number} slotIndex 
 * @returns {object|null}
 */
export function gatherPokemonDataAsJson(partyType, slotIndex) {
    const rawData = collectRawPokemonData(partyType, slotIndex);
    if (!rawData) {
        return null;
    }
    return createPokemon(rawData);
}

/**
 * 特定のパーティのデータを収集し、構造化されたJSONを返す
 * @param {string} partyType 
 * @returns {object}
 */
export function gatherPartyDataAsJson(partyType) {
    const members = [];
    for (let i = 0; i < 6; i++) {
        const pokemonData = gatherPokemonDataAsJson(partyType, i);
        if (pokemonData) {
            members.push(pokemonData);
        }
    }
    return createParty({ partyType, members });
}

/**
 * 特定のサイドのデータを収集し、構造化されたJSONを返す
 * @param {string} partyType 
 * @returns {object}
 */
export function gatherSideDataAsJson(partyType) {
    const partyData = gatherPartyDataAsJson(partyType);
    return createBattleSide({ partyType, party: partyData });
}