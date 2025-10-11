// trainedPokemon.js - 育成済みポケモン管理機能

import { escapeHTML, showAlert } from './utils.js';
import { updateAbilitiesForPokemon } from './formHelpers.js';

export class TrainedPokemonManager {
    constructor() {
        this.modal = document.getElementById('trained-pokemon-modal');
        this.tbody = document.getElementById('trained-pokemon-list-tbody');
        this.form = document.getElementById('pokemon-form');
        this.formModal = new bootstrap.Modal(document.getElementById('pokemon-form-modal'));
        this.showAddBtn = document.getElementById('show-add-pokemon-modal');
        this.evTotalEl = document.getElementById('ev-total');
        
        if (this.modal) {
            this.init();
        }
    }

    init() {
        this.modal.addEventListener('show.bs.modal', () => this.loadTrainedPokemons());
        
        if (this.showAddBtn) {
            this.showAddBtn.addEventListener('click', () => this.showPokemonForm());
        }
        
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        document.querySelectorAll('.ev-input').forEach(input => {
            input.addEventListener('change', () => this.updateEvTotal());
        });
    }

    async loadTrainedPokemons() {
        try {
            const response = await fetch('/api/trained-pokemons');
            if (!response.ok) throw new Error('Failed to fetch trained pokemons');
            const pokemons = await response.json();

            this.tbody.innerHTML = '';
            if (pokemons.length === 0) {
                this.tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">登録されているポケモンはいません。</td></tr>';
                return;
            }

            pokemons.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${p.id}</td>
                    <td>${escapeHTML(p.pokemon_name) || 'N/A'}</td>
                    <td>${escapeHTML(p.nickname) || ''}</td>
                    <td>${p.level}</td>
                    <td>${escapeHTML(p.tera_type_name) || 'N/A'}</td>
                    <td>${escapeHTML(p.item_name) || 'N/A'}</td>
                    <td>${escapeHTML(p.ability_name) || 'N/A'}</td>
                    <td>${escapeHTML(p.nature_name) || 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-light edit-btn" data-id="${p.id}"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${p.id}"><i class="bi bi-trash"></i></button>
                    </td>
                `;
                this.tbody.appendChild(tr);
            });

            this.attachActionListeners();

        } catch (error) {
            console.error('Error loading trained pokemons:', error);
            this.tbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">データの読み込みに失敗しました。</td></tr>';
        }
    }

    attachActionListeners() {
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleEditClick(e));
        });
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleDeleteClick(e));
        });
    }

    async handleEditClick(event) {
        const id = event.currentTarget.dataset.id;
        try {
            const response = await fetch(`/api/trained-pokemons/${id}`);
            if (!response.ok) throw new Error('Failed to fetch pokemon details');
            const pokemon = await response.json();
            await this.showPokemonForm(pokemon);
        } catch (error) {
            console.error(`Error fetching pokemon ${id}:`, error);
            alert('ポケモンの情報の取得に失敗しました。');
        }
    }

    async handleDeleteClick(event) {
        const id = event.currentTarget.dataset.id;
        if (confirm(`ID: ${id} のポケモンを本当に削除しますか?`)) {
            try {
                const response = await fetch(`/api/trained-pokemons/${id}`, { method: 'DELETE' });
                if (!response.ok) throw new Error('Failed to delete pokemon');
                showAlert('trained-pokemon-alert', 'ポケモンを削除しました。', 'success');
                this.loadTrainedPokemons();
            } catch (error) {
                console.error(`Error deleting pokemon ${id}:`, error);
                alert('削除に失敗しました。');
            }
        }
    }

    async showPokemonForm(pokemon = null) {
        this.form.reset();
        document.getElementById('pokemon-id').value = '';

        const fields = ['pokemon-master-id', 'nickname', 'tera-type-id', 'held-item-id', 'ability-id', 'nature-id', 'move1-id', 'move2-id', 'move3-id', 'move4-id', 'ev-hp', 'ev-atk', 'ev-def', 'ev-spa', 'ev-spd', 'ev-spe'];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });

        if (pokemon) {
            document.getElementById('pokemon-id').value = pokemon.id || '';
            document.getElementById('pokemon-master-id').value = pokemon.pokemon_id || '';
            document.getElementById('nickname').value = pokemon.nickname || '';
            document.getElementById('level').value = pokemon.level || 50;
            document.getElementById('tera-type-id').value = pokemon.tera_type_id || '';
            document.getElementById('held-item-id').value = pokemon.held_item_id || '';

            // The ability dropdown is now pre-populated with all master abilities.
            // The dynamic update is no longer needed.
            document.getElementById('ability-id').value = pokemon.ability_id || '';

            document.getElementById('nature-id').value = pokemon.nature_id || '';
            
            document.getElementById('ev-hp').value = pokemon.ev_hp || 0;
            document.getElementById('ev-atk').value = pokemon.ev_atk || 0;
            document.getElementById('ev-def').value = pokemon.ev_def || 0;
            document.getElementById('ev-spa').value = pokemon.ev_spa || 0;
            document.getElementById('ev-spd').value = pokemon.ev_spd || 0;
            document.getElementById('ev-spe').value = pokemon.ev_spe || 0;

            for (let i = 1; i <= 4; i++) {
                document.getElementById(`move${i}-id`).value = pokemon[`move${i}_id`] || '';
            }
        } else {
            // The ability dropdown is now pre-populated, no need to clear it.
        }
        
        this.updateEvTotal();
        this.formModal.show();
    }

    async handleFormSubmit(event) {
        event.preventDefault();
        const id = document.getElementById('pokemon-id').value;
        const formData = {
            pokemon_id: document.getElementById('pokemon-master-id').value,
            nickname: document.getElementById('nickname').value,
            level: document.getElementById('level').value,
            tera_type_id: document.getElementById('tera-type-id').value,
            held_item_id: document.getElementById('held-item-id').value,
            ability_id: document.getElementById('ability-id').value,
            nature_id: document.getElementById('nature-id').value,
            move1_id: document.getElementById('move1-id').value,
            move2_id: document.getElementById('move2-id').value,
            move3_id: document.getElementById('move3-id').value,
            move4_id: document.getElementById('move4-id').value,
            ev_hp: document.getElementById('ev-hp').value,
            ev_atk: document.getElementById('ev-atk').value,
            ev_def: document.getElementById('ev-def').value,
            ev_spa: document.getElementById('ev-spa').value,
            ev_spd: document.getElementById('ev-spd').value,
            ev_spe: document.getElementById('ev-spe').value,
        };

        const url = id ? `/api/trained-pokemons/${id}` : '/api/trained-pokemons';
        const method = id ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            if (!response.ok) throw new Error('Failed to save pokemon');
            this.formModal.hide();
            this.loadTrainedPokemons();
        } catch (error) {
            console.error('Error saving pokemon:', error);
            alert('保存に失敗しました。');
        }
    }

    updateEvTotal() {
        let total = 0;
        document.querySelectorAll('.ev-input').forEach(input => {
            total += Number(input.value) || 0;
        });
        this.evTotalEl.textContent = total;
        if (total > 510) {
            this.evTotalEl.classList.add('text-danger');
        } else {
            this.evTotalEl.classList.remove('text-danger');
        }
    }
}