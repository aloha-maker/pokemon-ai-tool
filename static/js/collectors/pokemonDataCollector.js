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

    return {
        name: slotElement.querySelector('.pokemon-input').value,
        ability: modal.querySelector('#details-ability-input').value,
        tera_type: modal.querySelector('#details-tera-type-select').value,
        item: modal.querySelector('#details-item-input').value,
        moves: moveIds,
        current_hp: hpBar ? parseFloat(hpBar.style.width) : 100,
        nature: modal.querySelector('#details-nature-select').value,
        ev: ev,
        boosts: boosts,
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
    // 1. 全てのセレクトボックスを取得
    const statusInputs = document.querySelectorAll('.pokemon-status-select');

    let partyData = []; // constだとエラーになるのでletにします
    let startIndex = 0;
    let endIndex = 0;

    // 2. 範囲を決める
    if (partyType === 'my-party') {
        startIndex = 0;
        endIndex = 6; // ※配列の0-5(6匹分)を取りたい場合は終了位置を「6」にします
    } else {
        startIndex = 6;
        endIndex = 12; // 6-11(6匹分)を取りたい場合は「12」
    }

    // 3. 配列を切り出して、ステータスを結合する
    // まず対象のポケモンたちを切り出し
    const slicedPokemons = detailedStates.slice(startIndex, endIndex);

    // mapを使って、各ポケモンにstatusプロパティを追加した新しい配列を作る
    partyData = slicedPokemons.map((pokemon, index) => {
        // 全体のinput配列から、対応する場所のinputを取得
        // (開始位置 + 現在のループ番号)
        const targetInput = statusInputs[startIndex + index];

        return {
            ...pokemon,            // もともとのポケモンのデータをコピー (名前など)
            status: targetInput ? targetInput.value : '' // セレクトボックスの値をセット
        };
    });
    return createBattleSide({ partyType, party: partyData });
}