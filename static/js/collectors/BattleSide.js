// BattleSide.js - BattleSideデータ構造を生成する

/**
 * BattleSideのJSONオブジェクトを生成する
 * @param {object} sideData - サイドのデータ
 * @param {string} sideData.partyType - 'my-party' or 'opponent-party'
 * @param {object} sideData.party - Partyオブジェクト
 * @returns {object} - 構造化されたBattleSideオブジェクト
 */
export function createBattleSide(sideData) {
    const {
        partyType,
        party
    } = sideData;

    // アクティブなポケモンを決定
    const key = partyType.replace("-party", "");
    const activePokemon = document.getElementById(key + '-active-pokemon').value;

    // BattleSideオブジェクトを構築
    return {
        team_name: partyType === 'my-party' ? 'Player' : 'Opponent',
        team: party,
        active: activePokemon,
        
        // 壁 (screens) の取得: チェックボックスなので checked を見る
        screens: {
            reflect: document.getElementById(key + '-reflect').checked,
            light_screen: document.getElementById(key + '-light-screen').checked,
            aurora_veil: document.getElementById(key + '-aurora-veil').checked,
        },
    
        // 設置技・その他 (side_conditions) の取得
        side_conditions: {
            // 数値入力は value を取得し、整数(int)に変換する (空欄やNaN対策で || 0 を入れると安全)
            spikes: parseInt(document.getElementById(key + '-spikes').value, 10) || 0,
            toxic_spikes: parseInt(document.getElementById(key + '-toxic-spikes').value, 10) || 0,
            
            // チェックボックス
            stealth_rock: document.getElementById(key + '-stealth-rock').checked,
            tailwind: document.getElementById(key + '-tailwind').checked,
        }
    };
}
