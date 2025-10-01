// partyGenerator.js - パーティ生成機能

import { escapeHTML, showAlert, setButtonLoading } from './utils.js';

export class PartyGenerator {
    constructor() {
        this.generateButton = document.getElementById('generate-party-button');
        this.registerButton = document.getElementById('register-generated-party-btn');
        this.lastGeneratedParty = null;
        
        if (this.generateButton) {
            this.init();
        }
    }

    init() {
        this.generateButton.addEventListener('click', () => this.handleGenerate());
        
        if (this.registerButton) {
            this.registerButton.addEventListener('click', () => this.handleRegister());
        }
    }

    async handleGenerate() {
        const availablePokemonEl = document.getElementById('available-pokemon');
        const conceptEl = document.getElementById('tactical-concept');
        const resultArea = document.getElementById('party-generation-result-area');
        const registerArea = document.getElementById('register-party-area');
        const registerAlert = document.getElementById('register-party-alert');

        const available_pokemon = availablePokemonEl.value
            .split('\n')
            .filter(p => p.trim() !== '');
        const concept = conceptEl.value;

        if (available_pokemon.length < 6) {
            alert('使用可能なポケモンを6体以上入力してください。');
            return;
        }
        if (!concept) {
            alert('戦術コンセプトを入力してください。');
            return;
        }

        setButtonLoading(this.generateButton, true);
        registerArea.classList.add('d-none');
        registerAlert.style.display = 'none';

        try {
            const response = await fetch('/generate-party', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ available_pokemon, concept }),
            });

            const data = await response.json();

            if (response.ok) {
                this.lastGeneratedParty = data.party;
                this.displayGeneratedParty(data, resultArea);
                registerArea.classList.remove('d-none');
            } else {
                resultArea.innerHTML = `<div class="alert alert-danger">エラー: ${data.error || '不明なエラー'}</div>`;
            }
        } catch (error) {
            console.error('パーティ生成APIの呼び出し中にエラーが発生しました:', error);
            resultArea.innerHTML = `<div class="alert alert-danger">APIの呼び出しに失敗しました。</div>`;
        } finally {
            setButtonLoading(this.generateButton, false);
        }
    }

    displayGeneratedParty(data, container) {
        let partyHtml = '<h5>提案パーティ</h5><div class="row g-2 mb-3">';
        data.party.forEach(p => {
            const movesHtml = p.moves.map(m => `<li>${escapeHTML(m.name)}</li>`).join('');
            partyHtml += `
                <div class="col-6">
                    <div class="glass-card p-2 small">
                        <div class="fw-bold">${escapeHTML(p.name)}</div>
                        <div class="text-muted">役割: ${escapeHTML(p.role)}</div>
                        <div><strong>持ち物:</strong> ${escapeHTML(p.item_name)}</div>
                        <div><strong>特性:</strong> ${escapeHTML(p.ability_name)}</div>
                        <div><strong>性格:</strong> ${escapeHTML(p.nature_name)}</div>
                        <div><strong>テラス:</strong> ${escapeHTML(p.tera_type_name)}</div>
                        <ul class="list-unstyled small mt-1 mb-0"><strong>技:</strong>${movesHtml}</ul>
                    </div>
                </div>
            `;
        });
        partyHtml += '</div>';

        let manualHtml = '<h5>運用ガイド</h5>';
        manualHtml += `<div class="glass-card p-3 small">${data.manual.replace(/\n/g, '<br>')}</div>`;

        container.innerHTML = partyHtml + manualHtml;
    }

    async handleRegister() {
        if (!this.lastGeneratedParty) {
            alert('登録するパーティデータがありません。先にパーティを生成してください。');
            return;
        }

        const partyName = prompt('登録するパーティ名を入力してください:', 'AI生成パーティ');
        if (!partyName || partyName.trim() === '') {
            return;
        }

        const registerAlert = document.getElementById('register-party-alert');
        setButtonLoading(this.registerButton, true);

        try {
            const response = await fetch('/api/register-generated-party', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    party: this.lastGeneratedParty, 
                    party_name: partyName 
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                showAlert('register-party-alert', result.message, 'success');
            } else {
                showAlert('register-party-alert', `エラー: ${result.error}`, 'danger');
            }

        } catch (error) {
            showAlert('register-party-alert', '登録中に不明なエラーが発生しました。', 'danger');
        } finally {
            setButtonLoading(this.registerButton, false);
        }
    }
}
