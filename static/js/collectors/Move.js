// Move.js - Moveデータ構造を生成する

/**
 * Moveオブジェクトを生成する
 * @param {string} name - 技名
 * @returns {{name: string}}
 */
export function createMove(name) {
    // 現状、UIからは技名しか取得できないため、技名のみを持つオブジェクトを返す
    return { name };
}
