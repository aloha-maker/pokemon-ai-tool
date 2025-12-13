// pokemonDataCollector.js - 画面からポケモンデータを収集し、構造化するモジュール
import { createBattleSide } from './BattleSide.js';

/**
 * 特定のサイドのデータを収集し、構造化されたJSONを返す
 * @param {string} partyType 
 * @returns {object}
 */
export function gatherSideDataAsJson(partyType,detailedStates) {
    // 1. 全てのセレクトボックスを取得
    // const statusInputs = document.querySelectorAll('.pokemon-status-select');

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
            // status: targetInput ? targetInput.value : '' // セレクトボックスの値をセット
        };
    });
    const teamData = {
        members : partyData,
        name : partyType,
        description : "",
        party_id : ""
    }
    console.log('teamData',teamData)

    return createBattleSide({ partyType, party: teamData });
}