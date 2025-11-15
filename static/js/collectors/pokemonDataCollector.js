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
function collectRawPokemonData(partyType, slotIndex,detailedStates) {

    const slotSelector = `.pokemon-slot[data-party-type='${partyType}'][data-slot-index='${slotIndex}']`;
    const slotElement = document.querySelector(slotSelector);

    let state_index = slotIndex
    if(partyType == 'opponent-party'){
        state_index = slotIndex + 6
    }

    // スロットが存在しない、またはポケモン名が入力されていなければ対象外
    if (!slotElement || !slotElement.querySelector('.pokemon-input').value) {
        console.log("スロットが存在しない、またはポケモン名が入力されていなければ対象外")
        return null;
    }

    const state = detailedStates[state_index]
    
    // 注意: この実装は、モーダルに表示されている情報が対象スロットのものであることを前提としています。
    const modal = document.getElementById('pokemon-details-modal');
    const moveIds = state ? state.moves.map(m => m.id).filter(id => id !== null) : [];
    console.log('state',state)

    // const moveNodes = modal.querySelectorAll('.details-move-input');
    // const moves = [];
    // moveNodes.forEach(input => {
        
    //     if (input.value) {
    //         const move ={name : input.value}
    //         console.log('move',move)
    //         moves.push(move);
    //     }
    // });

    const hpBar = slotElement.querySelector('.hp-bar');

    // EVの収集
    const ev = {
        hp: parseInt(modal.querySelector('#details-ev-hp').value || '0', 10),
        atk: parseInt(modal.querySelector('#details-ev-atk').value || '0', 10),
        def: parseInt(modal.querySelector('#details-ev-def').value || '0', 10),
        spa: parseInt(modal.querySelector('#details-ev-spa').value || '0', 10),
        spd: parseInt(modal.querySelector('#details-ev-spd').value || '0', 10),
        spe: parseInt(modal.querySelector('#details-ev-spe').value || '0', 10),
    };

    // Boostsの収集
    const boosts = {
        atk: parseInt(modal.querySelector('#details-boost-atk').value || '0', 10),
        def: parseInt(modal.querySelector('#details-boost-def').value || '0', 10),
        spa: parseInt(modal.querySelector('#details-boost-spa').value || '0', 10),
        spd: parseInt(modal.querySelector('#details-boost-spd').value || '0', 10),
        spe: parseInt(modal.querySelector('#details-boost-spe').value || '0', 10),
    };

    return {
        name: slotElement.querySelector('.pokemon-input').value,
        ability: modal.querySelector('#details-ability-input').value,
        tera_type: modal.querySelector('#details-tera-type-select').value,
        item: modal.querySelector('#details-item-input').value,
        moves: moveIds,
        current_hp: hpBar ? parseFloat(hpBar.style.width) : 100,
        nature: modal.querySelector('#details-nature-select').value, // 性格を追加
        ev: ev, // 努力値を追加
        boosts: boosts, // 能力ランクを追加
        status: slotElement.querySelector('.pokemon-status-select').value, // 状態異常を追加
    };
}

/**
 * 特定のスロットのポケモンデータを収集し、構造化されたJSONを返す
 * @param {string} partyType 
 * @param {number} slotIndex 
 * @returns {object|null}
 */
export function gatherPokemonDataAsJson(partyType, slotIndex,detailedStates) {
    const rawData = collectRawPokemonData(partyType, slotIndex,detailedStates);
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
export function gatherPartyDataAsJson(partyType,detailedStates) {
    const members = [];
    for (let i = 0; i < 6; i++) {
        const pokemonData = gatherPokemonDataAsJson(partyType, i,detailedStates);
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
export function gatherSideDataAsJson(partyType,detailedStates) {
    const partyData = gatherPartyDataAsJson(partyType,detailedStates);
    return createBattleSide({ partyType, party: partyData });
}