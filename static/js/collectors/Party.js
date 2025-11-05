// Party.js - Partyデータ構造を生成する

/**
 * PartyのJSONオブジェクトを生成する
 * @param {object} partyData - パーティのデータ
 * @param {string} partyData.partyType - 'my-party' or 'opponent-party'
 * @param {object[]} partyData.members - Pokemonオブジェクトの配列
 * @returns {object} - 構造化されたPartyオブジェクト
 */
export function createParty(partyData) {
    const {
        partyType,
        members
    } = partyData;

    return {
        name: partyType === 'my-party' ? 'My Battle Party' : 'Opponent Party',
        description: 'Collected during battle analysis',
        party_id: null, // 新規作成のためIDはnull
        members: members || []
    };
}
