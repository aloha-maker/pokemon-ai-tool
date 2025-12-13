// BattleState.js - BattleStateデータ構造を生成する

/**
 * BattleFieldのデフォルトJSONオブジェクトを生成する
 * @returns {object}
 */
function createDefaultBattleField() {
    return {
        weather: null,
        terrain: null,
        turn: 0,
        is_double: false,
        last_move_user: null,
        last_move_name: null,
        last_move_side: null
    };
}

/**
 * BattleStateのJSONオブジェクトを生成する
 * @param {object} stateData - バトル状態のデータ
 * @param {object} stateData.side1 - プレイヤー側のBattleSideオブジェクト
 * @param {object} stateData.side2 - 相手側のBattleSideオブジェクト
 * @returns {object} - 構造化されたBattleStateオブジェクト
 */
export function createBattleState(stateData) {
    const {
        side1,
        side2
    } = stateData;

    return {
        side1: side1,
        side2: side2,
        field: createDefaultBattleField(),
        is_side1_attacker: true // 仮に自分側が攻撃側として設定
    };
}
