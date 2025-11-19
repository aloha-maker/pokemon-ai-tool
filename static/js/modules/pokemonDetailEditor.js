import { populateSelect } from './formHelpers.js';

function calculateMaxPP(basePP) {
    const pp = Number(basePP);
    if (isNaN(pp)) return 0;
    if (pp === 1) return 1;
    return Math.floor(pp * 1.6);
}

// This can be cached to avoid re-fetching
let pokemonMasterList = [];
async function getPokemonByName(name) {
    if (pokemonMasterList.length === 0) {
        try {
            const response = await fetch('/api/master/pokemons');
            const pokemonData = await response.json();
            if (pokemonData.status === 'success') {
                pokemonMasterList = pokemonData.data.pokemons;
            }
        } catch (e) {
            console.error("Failed to fetch pokemon master list", e);
            return null;
        }
    }
    return pokemonMasterList.find(p => p.name_ja === name) || null;
}

async function getPokemonIdByName(name) {
    const pokemon = await getPokemonByName(name);
    return pokemon ? pokemon.id : null;
}


async function getAllMoves() {
    try {
        const response = await fetch(`/api/master/moves`);
        if (!response.ok) return [];
        const movesData = await response.json();
        return movesData.data.moves;
    } catch (error) {
        console.error(`Error fetching moves:`, error);
        return [];
    }
}

async function getAllAbilities() {
    try {
        const response = await fetch(`/api/master/abilities`);
        if (!response.ok) return [];
        const abilitiesData = await response.json();
        return abilitiesData.data.abilities;
    } catch (error) {
        console.error(`Error fetching abilities:`, error);
        return [];
    }
}

export class PokemonDetailEditor {
    constructor() {
        this.modal = new bootstrap.Modal(document.getElementById('pokemon-details-modal'));
        this.pokemonSlots = document.querySelectorAll('.pokemon-slot');
        this.modalElement = document.getElementById('pokemon-details-modal');
        this.pokemonNameEl = document.getElementById('details-pokemon-name');
        
        // --- 追加 ---
        this.teraTypeSelect = document.getElementById('details-tera-type-select');
        this.itemInput = document.getElementById('details-item-input');
        this.natureSelect = document.getElementById("details-nature-select");
        this.typesList = [];
        this.itemsList = [];
        this.naturesList = [];
        // --- ここまで ---

        this.abilityInput = document.getElementById('details-ability-input');
        this.abilitiesList = [];
        this.moveInputs = document.querySelectorAll('.details-move-input');
        this.movesList = [];
        this.ppInputs = document.querySelectorAll('.pp-input');
        this.ppBtns = document.querySelectorAll('.pp-btn');
        this.saveBtn = document.getElementById('save-pokemon-details-btn');
        this.currentSlot = null;

        this.partyState = Array(12).fill(null).map(() => ({
            // サーバーの members[*].ability （文字列ID）
            ability: null, // 例: "289"
        
            // 種族値
            base_stats: {
                hp: 0,
                atk: 0,
                def: 0,
                spa: 0,
                spd: 0,
                spe: 0
            },
        
            // ランク補正
            boosts: {
                atk: 0,
                def: 0,
                spa: 0,
                spd: 0,
                spe: 0
            },
        
            // 実数値
            calculated_stats: {
                hp: 0,
                atk: 0,
                def: 0,
                spa: 0,
                spd: 0,
                spe: 0
            },
        
            current_hp: 0,
        
            // 努力値
            ev: {
                hp: 0,
                atk: 0,
                def: 0,
                spa: 0,
                spd: 0,
                spe: 0
            },
        
            // サーバーの members[*].item （文字列ID）
            item: null, // 例: "683"
        
            // 個体値
            iv: {
                hp: 31,
                atk: 31,
                def: 31,
                spa: 31,
                spd: 31,
                spe: 31
            },
        
            level: 50,
            max_hp: 0,
        
            // 技配列（4つ分）
            moves: Array(4).fill(null).map(() => ({
                accuracy: null,      // 例: 100
                category: null,      // "physical" | "special" | "status"
                contact: false,
                crit_rate: null,     // クリ率（そのまま入れるなら number）
                effect: null,
                name: "",            // 技名（日本語）
                power: 0,
                pp: null,
                type: null           // "electric" など
            })),
        
            // ポケモン名（日本語）
            name: "",
        
            // 性格名（日本語）: サーバーと同じく文字列で保持
            nature: "まじめ",
        
            status: null,      // 例: "par", "brn" など想定
            tera_type: null,   // 例: "electric" など（現状 null）
            types: []          // 例: ["electric", "dragon"]
        }));
        
        

        this.init();
    }

    async init() {
        // --- 追加 ---
        await this.loadMasterData();
        this.populateMasterDataForms();
        // --- ここまで ---

        this.pokemonSlots.forEach((slot, index) => {
            const gearIcon = slot.querySelector('.pokemon-settings-icon');
            if (gearIcon) {
                gearIcon.addEventListener('click', () => {
                    this.currentSlot = index;
                    this.openModalFor(slot);
                });
            }
        });

        this.moveInputs.forEach((input, index) => {
            input.addEventListener('input', (e) => {
                const moveName = e.target.value;
                const move = this.movesList.find(m => (m.name_ja || m.name) === moveName);
                const ppInput = this.ppInputs[index];

                if (move && ppInput) {
                    // 技が見つかれば、その技の最大PPをPP入力欄に設定
                    const maxPP = calculateMaxPP(move.pp);
                    ppInput.value = maxPP;
                }
            });
        });

        this.ppBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                const input = e.currentTarget.parentElement.querySelector('.pp-input');
                let currentValue = parseInt(input.value, 10);
                if (action === 'increment') {
                    currentValue++; // Should be capped at max PP
                } else {
                    currentValue = Math.max(0, currentValue - 1);
                }
                input.value = currentValue;
            });
        });

        this.saveBtn.addEventListener('click', () => this.saveDetails());

        document.addEventListener('partyLoaded', (e) => {
            this.updateStateFromLoadedParty(e.detail);
        });

        this.modalElement.addEventListener('hide.bs.modal', () => {
            this.resetAbilitiesDatalist();
        });
    }

    // --- 新規メソッド ---
    async loadMasterData() {
        try {
            const [typesRes, itemsRes, naturesRes] = await Promise.all([
                fetch('/api/master/types'),
                fetch('/api/master/items'),
                fetch('/api/master/natures')
            ]);
            const typesData = await typesRes.json();
            if (typesData.status === 'success') {
                this.typesList = typesData.data.types;
            }
            const itemsData = await itemsRes.json();
            if (itemsData.status === 'success') {
                this.itemsList = itemsData.data.items;
            }
            const naturesData = await naturesRes.json();
            if (naturesData.status === 'success') {
                this.naturesList = naturesData.data.natures;
            }
        } catch (error) {
            console.error("Failed to load master data:", error);
        }
    }

    populateMasterDataForms() {
        // Populate Tera Type select
        this.teraTypeSelect.innerHTML = '<option value="">テラスタイプを選択</option>';
        this.typesList.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id; // IDをvalueに設定
            option.textContent = type.name_ja;
            this.teraTypeSelect.appendChild(option);
        });

        // Populate Tera Type select
        this.natureSelect.innerHTML = '<option value="">性格を選択</option>';
        this.naturesList.forEach(type => {
            const option = document.createElement('option');
            option.value = type.id; // IDをvalueに設定
            option.textContent = type.name_ja;
            this.natureSelect.appendChild(option);
        });

        // Populate Item datalist
        const itemDatalist = document.getElementById('item-datalist');
        if (itemDatalist) {
            itemDatalist.innerHTML = '';
            this.itemsList.forEach(item => {
                const option = document.createElement('option');
                option.value = item.name_ja;
                itemDatalist.appendChild(option);
            });
        }
    }

    async resetAbilitiesDatalist() {
        const abilityDatalist = document.getElementById('ability-datalist');
        if (!abilityDatalist) return;

        // 全特性リストがキャッシュされていなければ取得
        if (this.abilitiesList.length === 0) {
            this.abilitiesList = await getAllAbilities();
        }

        abilityDatalist.innerHTML = '';
        this.abilitiesList.forEach(ability => {
            const option = document.createElement('option');
            option.value = ability.name_ja || ability.name;
            abilityDatalist.appendChild(option);
        });
    }
    updateStateFromLoadedParty(members) {
        for (let i = 0; i < members.length; i++) {
            const m = members[i];
            const slot = this.partyState[i];
    
            if (!m) continue;
    
            slot.ability = m.ability ?? null;
            slot.base_stats = { ...m.base_stats };
            slot.boosts = { ...m.boosts };
            slot.calculated_stats = { ...m.calculated_stats };
            slot.current_hp = m.current_hp ?? 0;
            slot.ev = { ...m.ev };
            slot.item = m.item ?? null;
            slot.iv = { ...m.iv };
            slot.level = m.level ?? 50;
            slot.max_hp = m.max_hp ?? 0;
    
            // moves（4つ分）
            slot.moves = m.moves.map(move => ({
                accuracy: move.accuracy ?? null,
                category: move.category ?? null,
                contact: move.contact ?? false,
                crit_rate: move.crit_rate ?? null,
                effect: move.effect ?? null,
                name: move.name ?? "",
                power: move.power ?? 0,
                pp: move.pp ?? 0,
                type: move.type ?? null
            }));
    
            slot.name = m.name ?? "";
            slot.nature = m.nature ?? "1";
            slot.status = m.status ?? null;
            slot.tera_type = m.tera_type ?? null;
            slot.types = m.types ? [...m.types] : [];

            this.updateSlotUI(i);
        }
    }
    

    async openModalFor(slot) {
        const pokemonName = slot.querySelector('.pokemon-input').value.trim();
        if (!pokemonName) {
            alert('先にポケモン名を入力してください。');
            return;
        }

        this.pokemonNameEl.textContent = pokemonName;

        const pokemonId = await getPokemonIdByName(pokemonName);
        if (!pokemonId) {
            alert(`ポケモン「${pokemonName}」がマスターデータに見つかりません。`);
            return;
        }
        console.log(`Pokemon: ${pokemonName}, ID: ${pokemonId}`);

        // このポケモンの特性リストを取得してdatalistを更新
        const abilityDatalist = document.getElementById('ability-datalist'); // グローバルなdatalistを参照
        if (abilityDatalist) {
            try {
                const response = await fetch(`/api/pokemon/${pokemonId}/abilities`);
                if (!response.ok) throw new Error('特性リストの取得に失敗しました。');
                const abilitiesData = await response.json();
                if (abilitiesData.status === 'success') {
                    const abilities = abilitiesData.data.abilities;
                    abilityDatalist.innerHTML = ''; // 中身をクリア
                    abilities.forEach(ability => {
                        const option = document.createElement('option');
                        option.value = ability.name_ja || ability.name;
                        abilityDatalist.appendChild(option);
                    });
                }

            } catch (error) {
                console.error('Error fetching pokemon-specific abilities:', error);
                abilityDatalist.innerHTML = ''; // エラー時は空にする
            }
        }

        // このポケモンの技リストを取得してdatalistを更新
        const moveDatalist = document.getElementById('move-datalist'); // グローバルなdatalistを参照
        if (moveDatalist) {
            try {
                const response = await fetch(`/api/pokemon/${pokemonId}/moves`);
                if (!response.ok) throw new Error('技リストの取得に失敗しました。');
                const movesData = await response.json();
                if (movesData.status === 'success') {
                    const moves = movesData.data.moves;
                    moveDatalist.innerHTML = ''; // 中身をクリア
                    moves.forEach(move => {
                        const option = document.createElement('option');
                        option.value = move.name_ja || move.name;
                        moveDatalist.appendChild(option);
                    });
                }

            } catch (error) {
                console.error('Error fetching pokemon-specific moves:', error);
                moveDatalist.innerHTML = ''; // エラー時は空にする
            }
        }

        // Cache abilities and moves lists if not already cached
        if (this.abilitiesList.length === 0) {
            this.abilitiesList = await getAllAbilities();
        }
        if (this.movesList.length === 0) {
            this.movesList = await getAllMoves();
        }
        
        const state = this.partyState[this.currentSlot];
        if (state) {
            // Item / Tera / Nature
            this.teraTypeSelect.value = state.tera_type || '';
            this.natureSelect.value = state.nature || '';
            const item = this.itemsList.find(i => i.id == state.item);
            this.itemInput.value = item ? item.name_ja : '';

            // Ability
            const ability = this.abilitiesList.find(a => a.id == state.ability);
            this.abilityInput.value = ability ? (ability.name_ja || ability.name) : '';

            // EVs
            document.getElementById('details-ev-hp').value = state.ev.hp || 0;
            document.getElementById('details-ev-atk').value = state.ev.atk || 0;
            document.getElementById('details-ev-def').value = state.ev.def || 0;
            document.getElementById('details-ev-spa').value = state.ev.spa || 0;
            document.getElementById('details-ev-spd').value = state.ev.spd || 0;
            document.getElementById('details-ev-spe').value = state.ev.spe || 0;

            // 技とPP
            this.moveInputs.forEach((input, i) => {
                const ppInput = this.ppInputs[i];
                const move = state.moves[i];
                if (move) {
                    input.value = move.name || '';
                    ppInput.value = (move.pp !== undefined && move.pp !== null) 
                        ? move.pp 
                        : (move.power ? calculateMaxPP(move.power) : 8);
                } else {
                    input.value = '';
                    ppInput.value = 8;
                }
            });
        }

        this.modal.show();
    }

    saveDetails() {
        // state からサーバー送信用 payload を作る
        const members = this.partyState.map(slot => ({
            ability: slot.ability,
            base_stats: { ...slot.base_stats },
            boosts: { ...slot.boosts },
            calculated_stats: { ...slot.calculated_stats },
            current_hp: slot.current_hp,
            ev: { ...slot.ev },
            item: slot.item,
            iv: { ...slot.iv },
            level: slot.level,
            max_hp: slot.max_hp,
            moves: slot.moves.map(m => ({
                accuracy: m.accuracy,
                category: m.category,
                contact: m.contact,
                crit_rate: m.crit_rate,
                effect: m.effect,
                name: m.name,
                power: m.power,
                pp: m.pp,
                type: m.type
            })),
            name: slot.name,
            nature: slot.nature,
            status: slot.status,
            tera_type: slot.tera_type,
            types: [...slot.types]
        }));
    
        this.updateSlotUI(this.currentSlot);
        this.modal.hide();
    }
    

    saveDetails() {
        const s = this.partyState[this.currentSlot];
    
        // ポケモン名 / ID（既存処理と同じ）
        const name = document.querySelector('#details-pokemon-name').textContent;
        s.pokemon_name = name;
        s.pokemon_id = getPokemonIdByName(name); // 非同期なら await 必要
    
        // ability
        const abilityName = this.abilityInput.value.trim();
        const ability = this.abilitiesList.find(a => (a.name_ja || a.name) === abilityName);
        s.ability_id = ability?.id ?? null;
    
        // item & tera
        const itemName = this.itemInput.value.trim();
        const item = this.itemsList.find(i => i.name_ja === itemName);
        s.held_item_id = item?.id ?? null;
    
        s.tera_type_id = this.teraTypeSelect.value ? Number(this.teraTypeSelect.value) : null;

        // nature
        s.nature = this.natureSelect.value ? Number(this.natureSelect.value) : null;
    
        // EVs
        s.ev = {
            hp: +document.getElementById('details-ev-hp').value || 0,
            atk: +document.getElementById('details-ev-atk').value || 0,
            def: +document.getElementById('details-ev-def').value || 0,
            spa: +document.getElementById('details-ev-spa').value || 0,
            spd: +document.getElementById('details-ev-spd').value || 0,
            spe: +document.getElementById('details-ev-spe').value || 0,
        };
    
        // moves
        this.moveInputs.forEach((input, i) => {
            const moveName = input.value.trim();
            const move = this.movesList.find(m => (m.name_ja || m.name) === moveName);
    
            s.moves[i].id = move?.id ?? null;
            s.moves[i].pp = Number(this.ppInputs[i].value) || null;
        });
    
        this.updateSlotUI(this.currentSlot);
        this.modal.hide();
    }
    

    async updateSlotUI(slotIndex) {
        const slot = this.pokemonSlots[slotIndex];
        if (!slot) return;

        const state = this.partyState[slotIndex];
        if (!state) return;

        // Get pokemon name from the UI to fetch its full data
        const pokemonName = slot.querySelector('.pokemon-input')?.value;
        const pokemonData = pokemonName ? await getPokemonByName(pokemonName) : null;

        // Update Item
        const itemNameSpan = slot.querySelector('.item-name');
        const itemIcon = slot.querySelector('.item-icon');
        const item = this.itemsList.find(i => i.id === Number(state.item));
        if (item && itemNameSpan && itemIcon) {
            itemNameSpan.textContent = item.name_ja;
            itemNameSpan.classList.remove('text-muted');
            if (item.name) {
                const iconFileName = item.name.toLowerCase().replace(/ /g, '-');
                itemIcon.src = `/static/item_icons/${iconFileName}.png`;
                itemIcon.onerror = () => {
                    itemIcon.src = 'https://placehold.co/24x24/333/ccc?text=?';
                };
            }
        } else if (itemNameSpan && itemIcon) {
            itemNameSpan.textContent = '持ち物';
            itemNameSpan.classList.add('text-muted');
            itemIcon.src = 'https://placehold.co/24x24/333/ccc?text=?';
        }

        // Update Tera Type
        const teraTypeNameSpan = slot.querySelector('.tera-type-name');
        const teraTypeIcon = slot.querySelector('.tera-type-icon');
        const teraType = this.typesList.find(t => t.id === Number(state.tera_type));
        if (teraType && teraTypeNameSpan && teraTypeIcon) {
            teraTypeNameSpan.textContent = teraType.name_ja;
            teraTypeNameSpan.classList.remove('text-muted');
            if (teraType.name) {
                // type_icons ディレクトリの命名規則に合わせる (小文字 + .png)
                const iconFileName = teraType.name.toLowerCase();
                teraTypeIcon.src = `/static/type_icons/${iconFileName}.png`;
                teraTypeIcon.onerror = () => { // 画像が見つからない場合
                    teraTypeIcon.src = 'https://placehold.co/24x24/333/ccc?text=?';
                };
            }
        } else if (teraTypeNameSpan && teraTypeIcon) {
            teraTypeNameSpan.textContent = 'テラスタイプ';
            teraTypeNameSpan.classList.add('text-muted');
            teraTypeIcon.src = 'https://placehold.co/24x24/333/ccc?text=?';
        }

        // Update Speed Stat
        const speedStatEl = slot.querySelector('.speed-stat-value');
        if (speedStatEl) {
            if (pokemonData) {
                speedStatEl.textContent = `S: ${pokemonData.speed}`;
                speedStatEl.classList.remove('text-muted');
            } else {
                speedStatEl.textContent = 'S: --';
                speedStatEl.classList.add('text-muted');
            }
        }
    }

    getState() {
        return this.partyState;
    }

    clearOpponentDetails() {
        // Opponent party is from index 6 to 11
        for (let i = 6; i < 12; i++) {
            this.partyState[i] = {
                ability_id: null,
                moves: [
                    { id: null, pp: null },
                    { id: null, pp: null },
                    { id: null, pp: null },
                    { id: null, pp: null },
                ]
            };
        }
        console.log('Opponent pokemon details cleared.');
    }
}