// calculator.js - ステータス・ダメージ計算機能

import { populateSelect } from './formHelpers.js';
import { debounce } from './utils.js';

export class Calculator {
    constructor() {
        this.modal = document.getElementById('calculator-modal');
        this.isInitialized = false;
        this.statusCalcForm = document.getElementById('status-calc-form');
        this.damageCalcForm = document.getElementById('damage-calc-form');
        
        if (this.modal) {
            this.modal.addEventListener('show.bs.modal', () => {
                if (!this.isInitialized) {
                    this.init();
                    this.isInitialized = true;
                }
            });
        }
    }

    async init() {
        const pokemonSelect = document.getElementById('calc-pokemon-id');
        const natureSelect = document.getElementById('calc-nature-id');
        const evInputs = this.statusCalcForm.querySelectorAll('.ev-calc-input');
        const evTotalEl = document.getElementById('ev-calc-total');

        // 初期プレースホルダー
        await Promise.all([
            populateSelect(pokemonSelect.id, [], 'ポケモンを選択...'),
            populateSelect(natureSelect.id, [], '性格を選択...'),
            populateSelect('attacker-move-id', [], '技を選択...'),
            populateSelect('attacker-pokemon-id', [], 'ポケモンを選択...'),
            populateSelect('defender-pokemon-id', [], 'ポケモンを選択...'),
            populateSelect('attacker-nature-id', [], '性格を選択...'),
            populateSelect('defender-nature-id', [], '性格を選択...'),
        ]);

        try {
            const [pokemonsRes, naturesRes, movesRes] = await Promise.all([
                fetch('/api/master/pokemons'),
                fetch('/api/master/natures'),
                fetch('/api/master/moves')
            ]);
            const pokemons = await pokemonsRes.json();
            const natures = await naturesRes.json();
            const moves = await movesRes.json();

            // ステータス計算タブのセレクタ
            populateSelect(pokemonSelect.id, pokemons, 'ポケモンを選択...');
            populateSelect(natureSelect.id, natures, '性格を選択...');

            // ダメージ計算タブのセレクタ
            document.querySelectorAll('.calc-pokemon-selector').forEach(sel => 
                populateSelect(sel.id, pokemons, 'ポケモンを選択...')
            );
            document.querySelectorAll('.calc-nature-selector').forEach(sel => 
                populateSelect(sel.id, natures, '性格を選択...')
            );
            document.querySelectorAll('.calc-move-selector').forEach(sel => 
                populateSelect(sel.id, moves, '技を選択...')
            );

        } catch (error) {
            console.error('Calculator initialization failed:', error);
            document.getElementById('status-calc-result').innerHTML = 
                '<p class="text-danger">初期化に失敗しました。</p>';
        }

        // イベントリスナー設定
        this.statusCalcForm.addEventListener('change', debounce(() => this.calculateStatus(), 200));
        this.statusCalcForm.addEventListener('input', debounce(() => this.calculateStatus(), 200));
        evInputs.forEach(input => input.addEventListener('input', () => this.updateEvCalcTotal()));

        this.damageCalcForm.addEventListener('change', debounce(() => this.calculateDamage(), 200));
        this.damageCalcForm.addEventListener('input', debounce(() => this.calculateDamage(), 200));
    }

    async calculateStatus() {
        const resultEl = document.getElementById('status-calc-result');
        const pokemonId = document.getElementById('calc-pokemon-id').value;
        const natureId = document.getElementById('calc-nature-id').value;

        if (!pokemonId || !natureId) {
            resultEl.innerHTML = '<p class="text-muted">ポケモンと性格を選択してください。</p>';
            return;
        }

        const evInputs = this.statusCalcForm.querySelectorAll('.ev-calc-input');
        const statsOrder = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
        const evs = {};
        
        evInputs.forEach((input, index) => {
            const statKey = statsOrder[index];
            const backendStatKey = statKey
                .replace('atk', 'attack')
                .replace('def', 'defense')
                .replace('spa', 'sp_attack')
                .replace('spd', 'sp_defense')
                .replace('spe', 'speed');
            evs[backendStatKey] = parseInt(input.value, 10) || 0;
        });

        const data = {
            pokemon_id: parseInt(pokemonId, 10),
            level: parseInt(document.getElementById('calc-level').value, 10),
            nature_id: parseInt(natureId, 10),
            evs: evs
        };

        try {
            const response = await fetch('/api/calculate/status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Calculation failed');
            }

            const stats = await response.json();
            this.displayStatusResults(stats);

        } catch (error) {
            console.error('Status calculation error:', error);
            resultEl.innerHTML = `<p class="text-danger">計算エラー: ${error.message}</p>`;
        }
    }

    displayStatusResults(stats) {
        const resultEl = document.getElementById('status-calc-result');
        resultEl.innerHTML = `
            <table class="table table-sm table-borderless">
                <tbody>
                    <tr><th>HP</th><td>${stats.hp}</td></tr>
                    <tr><th>こうげき</th><td>${stats.attack}</td></tr>
                    <tr><th>ぼうぎょ</th><td>${stats.defense}</td></tr>
                    <tr><th>とくこう</th><td>${stats.sp_attack}</td></tr>
                    <tr><th>とくぼう</th><td>${stats.sp_defense}</td></tr>
                    <tr><th>すばやさ</th><td>${stats.speed}</td></tr>
                </tbody>
            </table>
        `;
    }

    async calculateDamage() {
        const damageResultEl = document.getElementById('damage-calc-result');
        const data = {
            attacker_level: parseInt(document.getElementById('attacker-level').value, 10) || 50,
            attack_stat: parseInt(document.getElementById('attacker-stat').value, 10) || 0,
            defender_hp: parseInt(document.getElementById('defender-hp').value, 10) || 0,
            defense_stat: parseInt(document.getElementById('defender-stat').value, 10) || 0,
            move_id: parseInt(document.getElementById('attacker-move-id').value, 10) || null,
            defender_id: parseInt(document.getElementById('defender-pokemon-id').value, 10) || null,
        };

        if (!data.attack_stat || !data.defender_hp || !data.defense_stat || !data.move_id || !data.defender_id) {
            damageResultEl.innerHTML = '<p class="text-muted">必須項目をすべて入力してください。</p>';
            return;
        }

        try {
            const response = await fetch('/api/calculate/damage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Calculation failed');
            }

            const result = await response.json();
            this.displayDamageResults(result);

        } catch (error) {
            console.error('Damage calculation error:', error);
            damageResultEl.innerHTML = `<p class="text-danger">計算エラー: ${error.message}</p>`;
        }
    }

    displayDamageResults(result) {
        const damageResultEl = document.getElementById('damage-calc-result');
        const hitsToKO = result.min_hits_to_ko === result.max_hits_to_ko ?
            (result.min_hits_to_ko === Infinity ? '∞' : `確定 ${result.min_hits_to_ko}発`):
            `乱数 ${result.min_hits_to_ko}発 〜 確定 ${result.max_hits_to_ko}発`;

        damageResultEl.innerHTML = `
            <div class="row">
                <div class="col-6">
                    <p class="mb-1">ダメージ: <strong>${result.min_damage} 〜 ${result.max_damage}</strong></p>
                    <p class="mb-0">割合: <strong>${result.min_damage_percent}% 〜 ${result.max_damage_percent}%</strong></p>
                </div>
                <div class="col-6">
                    <p class="mb-1">確定数: <strong>${hitsToKO}</strong></p>
                </div>
            </div>
        `;
    }

    updateEvCalcTotal() {
        const evInputs = this.statusCalcForm.querySelectorAll('.ev-calc-input');
        const evTotalEl = document.getElementById('ev-calc-total');
        let total = 0;
        evInputs.forEach(input => {
            total += parseInt(input.value, 10) || 0;
        });
        evTotalEl.textContent = total;
        evTotalEl.classList.toggle('text-danger', total > 510);
    }
}
