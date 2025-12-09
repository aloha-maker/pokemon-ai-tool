// simulator.js - バトルシミュレーター機能

import { populateSelect } from './formHelpers.js';
import { escapeHTML, setButtonLoading } from './utils.js';

export class Simulator {
    constructor() {
        this.modal = document.getElementById('simulator-modal');
        this.setupScreen = document.getElementById('simulation-setup-screen');
        this.selectionScreen = document.getElementById('simulation-selection-screen');
        this.battleScreen = document.getElementById('simulation-battle-screen');
        
        this.party1Select = document.getElementById('sim-party1-id');
        this.party2Select = document.getElementById('sim-party2-id');
        this.startBtn = document.getElementById('start-simulation-btn');
        this.nextTurnBtn = document.getElementById('next-turn-btn');
        this.logArea = document.getElementById('simulation-log-area');
        
        this.simulationId = null;
        
        if (this.modal) {
            this.init();
        }
    }

    init() {
        this.modal.addEventListener('show.bs.modal', () => {
            this.simulationId = null;
            this.updateUI({ state: 'INITIALIZED', log: ['対戦準備ボタンを押して開始してください。'] });
            this.nextTurnBtn.disabled = false;
            this.nextTurnBtn.innerHTML = '<span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span> ターンを進める';
            this.initPartySelectors();
        });

        if (this.startBtn) {
            this.startBtn.addEventListener('click', () => this.handleStartSimulation());
        }
        
        if (this.nextTurnBtn) {
            this.nextTurnBtn.addEventListener('click', () => this.handleNextTurn());
        }
    }

    async initPartySelectors() {
        try {
            const response = await fetch('/api/parties');
            if (!response.ok) throw new Error('パーティ一覧の取得に失敗しました。');
            const responseData = await response.json();
            if (responseData.status !== 'success') {
                throw new Error(responseData.message || 'パーティ一覧の取得に失敗しました。');
            }
            const parties = responseData.data;
            const options = parties.map(p => ({ id: p.id, name_ja: p.name }));
            populateSelect(this.party1Select.id, options, 'パーティを選択...');
            populateSelect(this.party2Select.id, options, 'パーティを選択...');
        } catch (error) {
            console.error(error);
            this.logArea.innerHTML = `<p class="text-danger">${error.message}</p>`;
        }
    }

    async handleStartSimulation() {
        const party1Id = this.party1Select.value;
        const party2Id = this.party2Select.value;

        if (!party1Id || !party2Id) {
            alert('2つのパーティを選択してください。');
            return;
        }

        setButtonLoading(this.startBtn, true);

        try {
            const response = await fetch('/api/simulations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ party1_id: party1Id, party2_id: party2Id })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'シミュレーションの作成に失敗しました。');
            }

            const data = await response.json();
            this.simulationId = data.simulation_id;
            this.updateUI(data.state);

        } catch (error) {
            console.error(error);
            this.logArea.innerHTML = `<p class="text-danger">${error.message}</p>`;
        } finally {
            setButtonLoading(this.startBtn, false);
        }
    }

    async handleNextTurn() {
        setButtonLoading(this.nextTurnBtn, true);
        try {
            const response = await fetch(`/api/simulations/${this.simulationId}/next_turn`, {
                method: 'POST'
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'ターン進行に失敗しました。');
            }
            const state = await response.json();
            this.updateUI(state);
        } catch (error) {
            console.error(error);
            this.logArea.innerHTML = `<p class="text-danger">${error.message}</p>`;
        } finally {
            setButtonLoading(this.nextTurnBtn, false);
        }
    }

    updateUI(state) {
        this.logArea.innerHTML = state.log.join('\n');
        this.logArea.scrollTop = this.logArea.scrollHeight;

        this.setupScreen.classList.toggle('d-none', state.state !== 'INITIALIZED');
        this.selectionScreen.classList.toggle('d-none', state.state !== 'SELECTING');
        this.battleScreen.classList.toggle('d-none', state.state !== 'READY_FOR_TURN' && state.state !== 'BATTLE_OVER');

        if (state.state === 'SELECTING') {
            this.renderSelectionScreen(state);
        } else if (state.state === 'READY_FOR_TURN' || state.state === 'BATTLE_OVER') {
            this.updateBattleField(state);
        }
        
        if (state.state === 'BATTLE_OVER') {
            this.nextTurnBtn.disabled = true;
            this.nextTurnBtn.textContent = `対戦終了 - 勝者: ${state.winner}`;
        }
    }

    renderSelectionScreen(state) {
        document.getElementById('party1-name-display').textContent = `パーティ1 (ID: ${state.party1.id})`;
        document.getElementById('party2-name-display').textContent = `パーティ2 (ID: ${state.party2.id})`;
        
        document.getElementById('party1-selection-list').innerHTML = this.renderSelectionList(state.party1.pokemons, 'party1');
        document.getElementById('party2-selection-list').innerHTML = this.renderSelectionList(state.party2.pokemons, 'party2');
    }

    renderSelectionList(pokemons, partyName) {
        return pokemons.map((p, index) => `
            <label class="list-group-item">
                <input class="form-check-input me-1" type="checkbox" value="${index}" name="${partyName}-selection">
                ${escapeHTML(p.nickname || p.pokemon_name)}
            </label>
        `).join('');
    }

    updateBattleField(state) {
        const p1 = state.party1.pokemons[state.party1.active_pokemon_index];
        const p2 = state.party2.pokemons[state.party2.active_pokemon_index];

        this.updatePokemonInfo('player', p1);
        this.updatePokemonInfo('opponent', p2);
    }

    updatePokemonInfo(playerType, pokemon) {
        const nameEl = document.getElementById(`${playerType}-pokemon-name`);
        const hpBarEl = document.getElementById(`${playerType}-pokemon-hp-bar`);
        const hpTextEl = document.getElementById(`${playerType}-pokemon-hp-text`);

        nameEl.textContent = pokemon.nickname || pokemon.pokemon_name;
        const hpPercent = (pokemon.current_hp / pokemon.max_hp) * 100;
        hpBarEl.style.width = `${hpPercent}%`;
        hpTextEl.textContent = `${pokemon.current_hp} / ${pokemon.max_hp}`;

        hpBarEl.classList.remove('bg-success', 'bg-warning', 'bg-danger');
        if (hpPercent > 50) {
            hpBarEl.classList.add('bg-success');
        } else if (hpPercent > 20) {
            hpBarEl.classList.add('bg-warning');
        } else {
            hpBarEl.classList.add('bg-danger');
        }
    }
}
