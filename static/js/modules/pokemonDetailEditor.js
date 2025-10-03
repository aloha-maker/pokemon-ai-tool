import { populateSelect } from './formHelpers.js';

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

async function getAbilitiesForPokemon(pokemonId) {
    if (!pokemonId) return [];
    try {
        const response = await fetch(`/api/pokemon/${pokemonId}/abilities`);
        if (!response.ok) return [];
        return await response.json();
    } catch (error) {
        console.error(`Error fetching abilities for pokemon ${pokemonId}:`, error);
        return [];
    }
}

export class PokemonDetailEditor {
    constructor() {
        this.modal = new bootstrap.Modal(document.getElementById('pokemon-details-modal'));
        this.pokemonSlots = document.querySelectorAll('.pokemon-slot');
        this.modalElement = document.getElementById('pokemon-details-modal');
        this.pokemonNameEl = document.getElementById('details-pokemon-name');
        this.abilitySelect = document.getElementById('details-ability-select');
        this.moveSelects = document.querySelectorAll('.details-move-select');
        this.ppInputs = document.querySelectorAll('.pp-input');
        this.ppBtns = document.querySelectorAll('.pp-btn');
        this.saveBtn = document.getElementById('save-pokemon-details-btn');
        this.currentSlot = null;

        this.partyState = Array(6).fill(null).map(() => ({
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
        const pokemonName = slot.querySelector('.pokemon-input').value;
        if (!pokemonName) {
            alert('先にポケモン名を入力してください。');
            return;
        }

        this.pokemonNameEl.textContent = pokemonName;

        const pokemonId = await getPokemonIdByName(pokemonName);
        if (!pokemonId) {
            alert('ポケモンが見つかりません。');
            return;
        }

        // Populate abilities and moves
        const abilities = await getAbilitiesForPokemon(pokemonId);
        populateSelect('details-ability-select', abilities, '特性を選択');

        const moves = await getAllMoves();
        this.moveSelects.forEach(select => {
            populateSelect(select.id, moves, '技を選択');
        });
        
        // Load state
        const state = this.partyState[this.currentSlot];
        if (state) {
            this.abilitySelect.value = state.ability_id || '';
            
            this.moveSelects.forEach((select, i) => {
                if (state.moves[i]) {
                    select.value = state.moves[i].id || '';
                }
            });
            this.ppInputs.forEach((input, i) => {
                if (state.moves[i]) {
                    input.value = state.moves[i].pp ?? '8'; 
                }
            });
        }

        this.modal.show();
    }

    saveDetails() {
        const state = this.partyState[this.currentSlot];
        state.ability_id = this.abilitySelect.value;
        this.moveSelects.forEach((select, i) => {
            state.moves[i].id = select.value;
            state.moves[i].pp = this.ppInputs[i].value;
        });

        console.log('Saved state for slot', this.currentSlot, this.partyState[this.currentSlot]);
        
        this.modal.hide();
    }
}
