import { populateSelect } from './formHelpers.js';

function calculateMaxPP(basePP) {
    const pp = Number(basePP);
    if (isNaN(pp)) return 0;
    if (pp === 1) return 1;
    return Math.floor(pp * 1.6);
}

// This can be cached to avoid re-fetching
let pokemonMasterList = [];
async function getPokemonIdByName(name) {
    if (pokemonMasterList.length === 0) {
        try {
            const response = await fetch('/api/master/pokemons');
            pokemonMasterList = await response.json();
        } catch (e) {
            console.error("Failed to fetch pokemon master list", e);
            return null;
        }
    }
    const pokemon = pokemonMasterList.find(p => p.name_ja === name);
    return pokemon ? pokemon.id : null;
}


async function getAllMoves() {
    try {
        const response = await fetch(`/api/master/moves`);
        if (!response.ok) return [];
        return await response.json();
    } catch (error) {
        console.error(`Error fetching moves:`, error);
        return [];
    }
}

async function getAllAbilities() {
    try {
        const response = await fetch(`/api/master/abilities`);
        if (!response.ok) return [];
        return await response.json();
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
        this.abilityInput = document.getElementById('details-ability-input');
        this.abilitiesList = [];
        this.moveInputs = document.querySelectorAll('.details-move-input');
        this.movesList = [];
        this.ppInputs = document.querySelectorAll('.pp-input');
        this.ppBtns = document.querySelectorAll('.pp-btn');
        this.saveBtn = document.getElementById('save-pokemon-details-btn');
        this.currentSlot = null;

        this.partyState = Array(12).fill(null).map(() => ({
            ability_id: null,
            moves: [
                { id: null, pp: null },
                { id: null, pp: null },
                { id: null, pp: null },
                { id: null, pp: null },
            ]
        }));

        this.init();
    }

    init() {
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
        members.forEach((member, index) => {
            if (index < this.partyState.length) {
                this.partyState[index] = {
                    ability_id: member.ability_id,
                    moves: [
                        { id: member.move1_id, pp: member.move1_pp },
                        { id: member.move2_id, pp: member.move2_pp },
                        { id: member.move3_id, pp: member.move3_pp },
                        { id: member.move4_id, pp: member.move4_pp },
                    ]
                };
            }
        });
        console.log('PokemonDetailEditor state updated from loaded party:', this.partyState);
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
                const abilities = await response.json();
                
                abilityDatalist.innerHTML = ''; // 中身をクリア
                abilities.forEach(ability => {
                    const option = document.createElement('option');
                    option.value = ability.name_ja || ability.name;
                    abilityDatalist.appendChild(option);
                });

            } catch (error) {
                console.error('Error fetching pokemon-specific abilities:', error);
                abilityDatalist.innerHTML = ''; // エラー時は空にする
            }
        }

        // Cache abilities and moves lists if not already cached
        if (this.abilitiesList.length === 0) {
            this.abilitiesList = await getAllAbilities();
        }
        if (this.movesList.length === 0) {
            this.movesList = await getAllMoves();
        }
        
        // Load state
        const state = this.partyState[this.currentSlot];
        console.log('Loading state for slot', this.currentSlot, state);
        if (state) {
            const ability = this.abilitiesList.find(a => a.id == state.ability_id);
            this.abilityInput.value = ability ? (ability.name_ja || ability.name) : '';
            console.log(`Set ability input to: ${this.abilityInput.value}`);
            
            this.moveInputs.forEach((input, i) => {
                const ppInput = this.ppInputs[i];
                let move = null;

                // 技名を設定
                if (state.moves[i] && state.moves[i].id) {
                    move = this.movesList.find(m => m.id == state.moves[i].id);
                    input.value = move ? (move.name_ja || move.name) : '';
                } else {
                    input.value = '';
                }

                // PPを設定
                if (state.moves[i] && state.moves[i].pp !== null && state.moves[i].pp !== undefined) {
                    // 1. 保存済みのPPがあればそれを最優先
                    ppInput.value = state.moves[i].pp;
                } else if (move) {
                    // 2. 保存済みPPがなく、技がセットされているなら、技マスタの最大PPをセット
                    const maxPP = calculateMaxPP(move.pp);
                    ppInput.value = maxPP;
                } else {
                    // 3. 技もセットされていなければ、デフォルト値（元の実装に合わせて8）
                    ppInput.value = '8';
                }
            });
        }

        this.modal.show();
    }

    saveDetails() {
        const state = this.partyState[this.currentSlot];
        
        const abilityName = this.abilityInput.value.trim();
        const ability = this.abilitiesList.find(a => (a.name_ja || a.name) === abilityName);
        state.ability_id = ability ? ability.id : null;

        this.moveInputs.forEach((input, i) => {
            const moveName = input.value.trim();
            const move = this.movesList.find(m => (m.name_ja || m.name) === moveName);
            state.moves[i].id = move ? move.id : null;
            state.moves[i].pp = this.ppInputs[i].value;
        });

        console.log('Saved state for slot', this.currentSlot, this.partyState[this.currentSlot]);
        
        this.modal.hide();
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