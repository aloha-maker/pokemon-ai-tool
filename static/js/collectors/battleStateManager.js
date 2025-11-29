// modules/partyStateManager.js
// 初期状態のデータ構造を定義します。これにより、createBattleState/createSide/createEmptySlotの可読性が向上します。
const EMPTY_SLOT_STATE = {
    id: null,
    pokemon_id: null,
    name: "",
    nickname: "",
    level: 50,
    base_stats: { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 },
    ev: { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 },
    iv: { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 },
    nature: null,
    nature_name: null,
    ability: null,
    ability_name: null,
    item: null,
    item_name: null,
    types: [],
    tera_type: null,
    tera_type_name: null,
    status: null,
    boosts: { atk: 0, def: 0, spa: 0, spd: 0, spe: 0 },
    max_hp: 100,
    current_hp: 0, // HPはパーセンテージで保持されることが多い
    moves: Array(4).fill(null).map(() => ({
        id: null,
        name: null,
        power: null,
        move_type: null,
        category: null,
        accuracy: null,
        pp: null,
        crit_rate: null,
        contact: null,
        effect: null
    })),
    calculated_stats: { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 }
};

const EMPTY_SIDE_STATE = {
    team_name: null,
    team: {
        name: null,
        description: null,
        members: Array(6).fill(null), // createEmptySlotで初期化
        party_id: null
    },
    active: null,
    screens: {
        reflect: null,
        light_screen: null,
        aurora_veil: null
    },
    side_conditions: {
        spikes: null,
        toxic_spikes: null,
        stealth_rock: null,
        tailwind: null
    }
};

const EMPTY_FIELD_STATE = {
    weather: null,
    terrain: null,
    turn: null,
    is_double: null,
};

/**
 * バトル全体の状態を管理し、HTML要素からデータをマッピングするクラス。
 */
export class BattleStateManager {
    constructor(masterData) {
        this.masterData = masterData;
        this.battleState = this.createBattleState();
        this.listeners = new Map();
        this.eventTarget = new EventTarget();
    }

    /**
     * 空のポケモンスロットオブジェクトを生成します。
     * @returns {object} ポケモンスロットの状態
     */
    createEmptySlot() {
        // ディープコピーで新しいオブジェクトを返します
        return JSON.parse(JSON.stringify(EMPTY_SLOT_STATE));
    }

    /**
     * 空のサイドオブジェクトを生成します。
     * @returns {object} バトルサイドの状態
     */
    createSide() {
        const side = JSON.parse(JSON.stringify(EMPTY_SIDE_STATE));
        // membersをcreateEmptySlotで初期化
        side.team.members = Array(6).fill(null).map(() => this.createEmptySlot());
        return side;
    }

    /**
     * 初期バトル状態オブジェクトを生成します。
     * @returns {object} バトル全体の初期状態
     */
    createBattleState() {
        return {
            side1: this.createSide(),
            side2: this.createSide(),
            field: JSON.parse(JSON.stringify(EMPTY_FIELD_STATE))
        };
    }

    /**
     * サイドごとのデータ（チーム、アクティブ、壁、設置技）をマッピングします。
     * HTMLから読み取った情報を既存の状態にマージすることで、データの損失を防ぎます。
     * @param {object} sideState - 更新対象のBattleState側のサイド状態
     * @param {Array<object>} sourceParty - HTMLから取得したデータソースのパーティメンバー配列
     * @param {object} sourceEnv - HTMLから取得した環境データ（自サイドまたは相手サイド）
     * @param {string} constantName - CONSTANTSからチーム名を取得するためのキー
     */
    _mapSideData(sideState, sourceParty, sourceEnv, constantName) {
        // 基本情報
        sideState.team_name = this.masterData.CONSTANTS[constantName];
        sideState.team.name = "";
        sideState.team.description = "";
        sideState.team.party_id = 0;

        // HTMLから読み取ったパーティ情報(sourceParty)を、既存のバトル状態(sideState.team.members)にマージします。
        // これにより、levelやEVなどの詳細情報を維持しつつ、画面上の変更を反映します。
        sideState.team.members.forEach((member, i) => {
            const source = sourceParty[i];
            if (source) {
                // `Object.assign` を使い、sourceのプロパティをmemberに上書き・追加します。
                Object.assign(member, source);
            }
        });

        // 環境条件の自動マッピング (Keys: light_screen -> lightScreen)
        const mapAndAssign = (target, source) => {
            Object.keys(target).forEach(key => {
                // スネークケースをキャメルケースに変換し、環境オブジェクトから値を取得
                const envKey = key.replace(/_(\w)/g, (match, p1) => p1.toUpperCase());
                if (envKey in source) {
                    target[key] = source[envKey];
                }
            });
        };

        sideState.active = sourceEnv.activePokemon;

        // スクリーン条件のマッピング
        mapAndAssign(sideState.screens, sourceEnv);

        // サイドコンディションのマッピング
        mapAndAssign(sideState.side_conditions, sourceEnv);
    }

    /**
     * HTMLから全てのデータを取得し、BattleStateオブジェクトを構築して返します。
     * @returns {object} 構築されたBattleStateオブジェクト
     */
    getBattleState() {
        const parties = this.getAllPokemonSlotConfigs();
        const environment = this.getBattleEnvironmentInput();
        const bs = this.battleState;

        // 1. 自分側の情報 (side1) のマッピング
        this._mapSideData(
            bs.side1,
            parties.myParty,
            environment.mySide,
            'MY_PARTY' // this.masterData.CONSTANTS.MY_PARTY
        );

        // 2. 相手側の情報 (side2) のマッピング
        this._mapSideData(
            bs.side2,
            parties.opponentParty,
            environment.opponentSide,
            'OPPONENT_PARTY' // this.masterData.CONSTANTS.OPPONENT_PARTY
        );
        
        // 3. フィールド全体の情報
        Object.assign(bs.field, {
            weather: environment.field.weather,
            terrain: environment.field.terrain,
            turn: environment.field.turn,
            is_double: environment.field.isDouble,
        });
        return bs;
    }

    // html -> js
    // すべてのポケモンスロットの設定を取得（自パーティと相手パーティを区別）
    getAllPokemonSlotConfigs() {
        const myPartyConfigs = this.getPartySlotConfigs('my-party');
        const opponentPartyConfigs = this.getPartySlotConfigs('opponent-party');
        
        return {
            myParty: myPartyConfigs,
            opponentParty: opponentPartyConfigs,
        };
    }

    // 特定のパーティタイプのスロット設定を取得
    getPartySlotConfigs(partyType) {
        const slotConfigs = [];
        const slotElements = document.querySelectorAll(`.pokemon-slot[data-party-type="${partyType}"]`);
        
        slotElements.forEach(slotElement => {
            const config = this.getPokemonSlotConfig(slotElement);
            slotConfigs.push(config);
        });
        
        // スロットインデックスでソート
        return slotConfigs.sort((a, b) => a.slotIndex - b.slotIndex);
    }

    // pokemon-slotの入力値
    getPokemonSlotConfig(slotElement){
        // 基本情報の取得
        const partyType = slotElement.dataset.partyType;
        const slotIndex = parseInt(slotElement.dataset.slotIndex);

         // ポケモン名の取得
        const pokemonInput = slotElement.querySelector('.pokemon-input');
        const pokemonName = pokemonInput.value || pokemonInput.placeholder;

        // HP関連の情報取得
        const hpBar = slotElement.querySelector('.hp-bar');
        const hpText = slotElement.querySelector('.hp-text');
        const hpPercentage = parseInt(hpBar.style.width);
        const hpTextValue = hpText.textContent; // %有りの文字列

        // アイテム情報の取得
        const itemIcon = slotElement.querySelector('.item-icon');
        const itemName = slotElement.querySelector('.item-name');
        const item = this.masterData.itemsList.find(i => i.name_ja === itemName.textContent);
        const itemInfo = {
            iconSrc: itemIcon.src,
            id: item?.id ?? null,
            name: itemName.textContent || '未設定',
            isVisible: !itemName.hidden
        };

        // テラスタルタイプ情報の取得
        const teraIcon = slotElement.querySelector('.tera-type-icon');
        const teraName = slotElement.querySelector('.tera-type-name');
        const tera = this.masterData.typesList.find(i => i.name_ja === teraName.textContent);
        const teraInfo = {
            iconSrc: teraIcon.src,
            id: tera?.id ?? null,
            name: teraName.textContent || '未設定',
            isVisible: !teraName.hidden
        };

        // 素早さ種族値の取得
        const speedStat = slotElement.querySelector('.speed-stat-value');
        const speedValue = speedStat.textContent.replace('S: ', '');
        
        // 状態異常の取得
        const statusSelect = slotElement.querySelector('.pokemon-status-select');
        const status = statusSelect.value;
        
        // スターターアイコンの状態
        const starterIcon = slotElement.querySelector('.starter-icon');
        const isStarter = !starterIcon.classList.contains('d-none');

        // pokemon-detailの入力値は詳細モーダルの確定時、パーティ読み込み時にsetDetailsで設定される

        // 設定値を更新
        return {
            name: pokemonName,
            item: itemInfo.id,
            item_name: itemInfo.name,
            tera_type: teraInfo.id,
            tera_type_name: teraInfo.name,
            status: status,
            current_hp: hpPercentage
        };
    }

    /**
     * ポケモン詳細モーダルからの入力値（能力値、技など）をバトル状態に設定します。
     * ロジックを統合し、インデックスの分岐処理を効率化しました。
     * @param {number} index - 0から11までのスロットインデックス
     * @param {object} detail - 詳細データ
     */
    setDetails(index, detail) {
        let memberArray;
        let memberIndex;

        if (index >= 0 && index <= 5) {
            // side1 (自パーティ)
            memberArray = this.battleState.side1.team.members;
            memberIndex = index;
        } else if (index >= 6 && index <= 11) {
            // side2 (相手パーティ)
            memberArray = this.battleState.side2.team.members;
            memberIndex = index - 6; // 正しいローカルインデックス
        } else {
            console.error(`Invalid slot index: ${index}`);
            return;
        }

        const p = memberArray[memberIndex];

        if (!p) {
            console.error(`Pokemon slot not found at index: ${index}`);
            return;
        }

        // 共通プロパティの代入を統合
        Object.assign(p, {
            name: detail.name,
            ability: detail.ability,
            base_stats: detail.base_stats,
            boosts: detail.boosts,
            calculated_stats: detail.calculated_stats,
            current_hp: detail.current_hp,
            ev: detail.ev,
            iv: detail.iv,
            level: detail.level,
            item: detail.item,
            max_hp: detail.max_hp,
            tera_type: detail.tera_type,
            nature: detail.nature,
            status: detail.status,
            types: detail.types,
            moves: detail.moves, // moves配列全体を上書き
        });

        // side1 (自パーティ) にのみ存在するboostsの代入（元のコードの差分を尊重）
        if (index >= 0 && index <= 5) {
            p.boosts = detail.boosts;
        }
    }

    /**
     * HTMLフォームからバトル環境設定の入力値を抽出し、構造化されたオブジェクトを返します。
     * @returns {object} 抽出されたバトル環境データ
     */
    getBattleEnvironmentInput() {
        // ヘルパー関数: IDで要素を取得し、値を取得する
        const getValue = (id) => document.getElementById(id).value;
        const getChecked = (id) => document.getElementById(id).checked;
    
        // 数値として取得するためのヘルパー関数
        const getNumberValue = (id) => {
            const value = document.getElementById(id).value;
            return parseInt(value, 10) || 0; // 数値に変換し、失敗した場合は0を返す
        };
    
        // --- 1. バトルフィールド設定 (Field & Global Conditions) ---
        const battleField = {
            weather: getValue('battle-weather'),
            terrain: getValue('battle-terrain'),
            turn: getNumberValue('battle-turn'),
            isDouble: getChecked('battle-is-double')
        };
    
        // --- 2. 自サイドの状態 (My Side Conditions) ---
        const mySideConditions = {
            activePokemon: getValue('my-active-pokemon'), // ポケモンのIDや名前など
            // 壁
            reflect: getChecked('my-reflect'),
            lightScreen: getChecked('my-light-screen'),
            auroraVeil: getChecked('my-aurora-veil'),
            // 設置技・その他
            spikes: getNumberValue('my-spikes'),
            toxicSpikes: getNumberValue('my-toxic-spikes'),
            stealthRock: getChecked('my-stealth-rock'),
            tailwind: getChecked('my-tailwind')
        };
    
        // --- 3. 相手サイドの状態 (Opponent Side Conditions) ---
        const opponentSideConditions = {
            activePokemon: getValue('opponent-active-pokemon'), // ポケモンのIDや名前など
            // 壁
            reflect: getChecked('opponent-reflect'),
            lightScreen: getChecked('opponent-light-screen'),
            auroraVeil: getChecked('opponent-aurora-veil'),
            // 設置技・その他
            spikes: getNumberValue('opponent-spikes'),
            toxicSpikes: getNumberValue('opponent-toxic-spikes'),
            stealthRock: getChecked('opponent-stealth-rock'),
            tailwind: getChecked('opponent-tailwind')
        };
    
        // --- 4. 最終オブジェクトの構築 ---
        const battleEnvironment = {
            field: battleField,
            mySide: mySideConditions,
            opponentSide: opponentSideConditions
        };
    
        return battleEnvironment;
    }
    
    // 単一スロットの取得
    getSlot(index) {
        if (index < 0 || index >= this.state.party.length) {
            console.error(`Invalid slot index: ${index}`);
            return null;
        }
        return this.state.party[index];
    }
    
    // 単一スロットの更新
    updateSlot(index, data) {
        if (index < 0 || index >= this.state.party.length) {
            console.error(`Invalid slot index: ${index}`);
            return false;
        }
        
        // Deep merge
        this.state.party[index] = {
            ...this.state.party[index],
            ...data,
            ev: { ...this.state.party[index].ev, ...(data.ev || {}) },
            iv: { ...this.state.party[index].iv, ...(data.iv || {}) },
            base_stats: { ...this.state.party[index].base_stats, ...(data.base_stats || {}) },
            calculated_stats: { ...this.state.party[index].calculated_stats, ...(data.calculated_stats || {}) },
            boosts: { ...this.state.party[index].boosts, ...(data.boosts || {}) },
            moves: data.moves ? [...data.moves] : this.state.party[index].moves
        };
        
        this.state.lastUpdate = Date.now();
        
        // イベント発火
        this.emit('slotUpdated', { index, data: this.state.party[index] });
        
        return true;
    }
    
    // パーティ全体の取得
    getParty() {
        return this.state.party;
    }
    
    // プレイヤーのパーティのみ取得 (0-5)
    getPlayerParty() {
        return this.state.party.slice(0, 6);
    }
    
    // 相手のパーティのみ取得 (6-11)
    getOpponentParty() {
        return this.state.party.slice(6, 12);
    }
    
    // パーティ全体の更新
    updateParty(partyData) {
        if (!Array.isArray(partyData)) {
            console.error('Party data must be an array');
            return false;
        }
        
        partyData.forEach((member, index) => {
            if (member && index < this.state.party.length) {
                this.updateSlot(index, member);
            }
        });
        
        this.emit('partyUpdated', { party: this.state.party });
        
        return true;
    }
    
    // 相手のパーティをクリア
    clearOpponentParty() {
        for (let i = 6; i < 12; i++) {
            this.state.party[i] = this.createEmptySlot();
        }
        
        this.emit('opponentCleared');
        
        return true;
    }
    
    // 特定のスロットをクリア
    clearSlot(index) {
        if (index < 0 || index >= this.state.party.length) {
            console.error(`Invalid slot index: ${index}`);
            return false;
        }
        
        this.state.party[index] = this.createEmptySlot();
        this.emit('slotCleared', { index });
        
        return true;
    }
    
    // パーティ全体をクリア
    clearAll() {
        this.state.party = Array(12).fill(null).map(() => this.createEmptySlot());
        this.emit('allCleared');
        
        return true;
    }
    
    // イベントリスナーの登録
    on(eventName, callback) {
        this.eventTarget.addEventListener(eventName, (e) => {
            callback(e.detail);
        });
    }
    
    // イベントリスナーの削除
    off(eventName, callback) {
        this.eventTarget.removeEventListener(eventName, callback);
    }
    
    // イベントの発火
    emit(eventName, detail) {
        const event = new CustomEvent(eventName, { detail });
        this.eventTarget.dispatchEvent(event);
    }
    
    // JSON形式でエクスポート
    export() {
        return JSON.parse(JSON.stringify(this.state));
    }
    
    // JSONからインポート
    import(data) {
        if (!data || !Array.isArray(data.party)) {
            console.error('Invalid import data');
            return false;
        }
        
        this.updateParty(data.party);
        return true;
    }
}