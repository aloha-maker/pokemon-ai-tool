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

    // アクティブなポケモンを決定（仮にパーティの先頭とする）
    const activePokemon = (party.members && party.members.length > 0) 
        ? party.members[0] 
        : null;

    // BattleSideオブジェクトを構築
    return {
        team_name: partyType === 'my-party' ? 'Player' : 'Opponent',
        team: party,
        active: activePokemon,
        
        // UIに存在しない項目はデフォルト値を設定
        screens: {
            reflect: false,
            light_screen: false,
            aurora_veil: false,
        },
        side_conditions: {
            spikes: 0,
            toxic_spikes: 0,
            stealth_rock: false,
            tailwind: false,
        }
    };
}
