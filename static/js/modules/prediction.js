// prediction.js - 選出予測機能

import { escapeHTML, setButtonLoading } from './utils.js';

export class PredictionManager {
    constructor() {
        this.predictButton = document.getElementById('predict-button');
        this.myPartySelect = document.getElementById('my-party-select');
        this.loadMyPartyBtn = document.getElementById('load-my-party-btn');
        this.myPartyDisplay = document.getElementById('my-party-display');
        this.activeDragBar = null;
        this.updateHpDisplayCallback = null;
        
        if (this.predictButton) {
            this.init();
        }
    }

    init() {
        this.initMyPartySelector();
        this.predictButton.addEventListener('click', () => this.handlePredict());
        
        if (this.loadMyPartyBtn) {
            this.loadMyPartyBtn.addEventListener('click', () => this.loadPartyToForm());
        }
        
        if (this.myPartyDisplay) {
            this.initPartyDisplay(this.myPartyDisplay);
        }
        const opponentPartyDisplay = document.getElementById('opponent-party-display');
        if (opponentPartyDisplay) {
            this.initPartyDisplay(opponentPartyDisplay);
        }

        // Add document-level listeners once
        document.addEventListener('mousemove', (e) => {
            if (this.activeDragBar && this.updateHpDisplayCallback) {
                const rect = this.activeDragBar.getBoundingClientRect();
                let newWidth = e.clientX - rect.left;
                let percentage = Math.round((newWidth / rect.width) * 100);
                percentage = Math.max(0, Math.min(100, percentage));
                this.updateHpDisplayCallback(percentage);
            }
        });

        document.addEventListener('mouseup', () => {
            this.activeDragBar = null;
            this.updateHpDisplayCallback = null;
        });
    }

    async initMyPartySelector() {
        if (!this.myPartySelect) return;
        
        try {
            const response = await fetch('/api/parties');
            if (!response.ok) throw new Error('パーティ一覧の取得に失敗しました。');
            const parties = await response.json();
            
            this.myPartySelect.innerHTML = '<option selected value="">登録済みパーティから選ぶ...</option>';
            parties.forEach(party => {
                const option = document.createElement('option');
                option.value = party.id;
                option.textContent = party.name;
                this.myPartySelect.appendChild(option);
            });
        } catch (error) {
            console.error(error);
        }
    }

    async loadPartyToForm() {
        const partyId = this.myPartySelect.value;
        if (!partyId) {
            alert('パーティを選択してください。');
            return;
        }

        try {
            const response = await fetch(`/api/parties/${partyId}`);
            if (!response.ok) throw new Error('パーティ情報の取得に失敗しました。');
            const party = await response.json();

            // Clear existing values
            const myPartySlots = document.querySelectorAll('#my-party-display .pokemon-slot');
            myPartySlots.forEach(slot => {
                slot.querySelector('.pokemon-input').value = '';
                const itemSelect = slot.querySelector('.item-select');
                if(itemSelect) {
                    itemSelect.value = '';
                    itemSelect.dispatchEvent(new Event('change'));
                }
                const teraSelect = slot.querySelector('.tera-type-select');
                if(teraSelect) {
                    teraSelect.value = '';
                    teraSelect.dispatchEvent(new Event('change'));
                }
            });

            // Populate new values
            party.members.forEach((member, index) => {
                if (index < myPartySlots.length) {
                    const slot = myPartySlots[index];
                    slot.querySelector('.pokemon-input').value = member.pokemon_name || '';

                    // アイコンを更新
                    const img = slot.querySelector('img');
                    if (img) {
                        const pokemonName = member.pokemon_name;
                        if (pokemonName) {
                            img.src = `/static/pokemon_icons/${pokemonName}.png`;
                            // 画像の読み込みに失敗した場合のフォールバック
                            img.onerror = () => {
                                img.src = `https://placehold.co/96x96/333/ccc?text=?`;
                                img.onerror = null;
                            };
                        } else {
                            const placeholderIndex = index + 1;
                            img.src = `https://placehold.co/96x96/333/ccc?text=P${placeholderIndex}`;
                        }
                    }
                    
                    const itemSelect = slot.querySelector('.item-select');
                    if (itemSelect) {
                        itemSelect.value = member.held_item_id || '';
                        itemSelect.dispatchEvent(new Event('change')); // To update icon
                    }

                    const teraSelect = slot.querySelector('.tera-type-select');
                    if (teraSelect) {
                        teraSelect.value = member.tera_type_id || '';
                        teraSelect.dispatchEvent(new Event('change')); // To update icon
                    }
                }
            });

            // Dispatch event for other modules to update their state
            const event = new CustomEvent('partyLoaded', { detail: party.members });
            document.dispatchEvent(event);

        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }

    initPartyDisplay(partyDisplayContainer) {
        const pokemonSlots = partyDisplayContainer.querySelectorAll('.pokemon-slot');

        pokemonSlots.forEach((slot, index) => {
            const img = slot.querySelector('img');
            const hpBarContainer = slot.querySelector('.hp-bar-container');
            const hpBar = slot.querySelector('.hp-bar');
            const hpText = slot.querySelector('.hp-text');
            const icon = slot.querySelector('.starter-icon');
            const pokemonInput = slot.querySelector('.pokemon-input');

            // ポケモン名入力イベントでアイコンを更新 (自・相手共通)
            if (pokemonInput && img) {
                const updateIcon = () => {
                    const pokemonName = pokemonInput.value.trim();
                    if (pokemonName) {
                        img.src = `/static/pokemon_icons/${pokemonName}.png`;
                        // 画像の読み込みに失敗した場合のフォールバック
                        img.onerror = () => {
                            img.src = `https://placehold.co/96x96/333/ccc?text=?`;
                            img.onerror = null; // エラーハンドラを一度きりにする
                        };
                    } else {
                        const placeholderIndex = index + 1;
                        img.src = `https://placehold.co/96x96/333/ccc?text=P${placeholderIndex}`;
                    }
                };

                pokemonInput.addEventListener('change', updateIcon);

                // 初期値がある場合に備えて、イベントを発火
                if (pokemonInput.value) {
                    updateIcon();
                }
            }


            // --- 1. 選出/先発のクリック処理 ---
            if (img) {
                img.style.cursor = 'pointer';
                img.dataset.clickState = '0';
                img.addEventListener('click', () => {
                    const currentState = parseInt(img.dataset.clickState, 10);
                    let nextState;

                    if (currentState === 0) { // 未選択 -> 選択
                        nextState = 1;
                        img.classList.add('pokemon-selected');
                        if (icon) icon.classList.add('d-none');
                    } else if (currentState === 1) { // 選択 -> 選択+先発
                        nextState = 2;
                        img.classList.add('pokemon-selected');
                        if (icon) icon.classList.remove('d-none');
                    } else { // 選択+先発 -> 未選択
                        nextState = 0;
                        img.classList.remove('pokemon-selected');
                        if (icon) icon.classList.add('d-none');
                    }
                    img.dataset.clickState = nextState.toString();
                });
            }

            // --- 2. HPバーのドラッグ処理 ---
            if (hpBarContainer) {
                const updateHpDisplay = (hpPercentage) => {
                    if (hpBar) {
                        hpBar.style.width = `${hpPercentage}%`;
                        hpBar.setAttribute('aria-valuenow', hpPercentage);
                        hpBar.classList.remove('bg-success', 'bg-warning', 'bg-danger');
                        if (hpPercentage > 50) {
                            hpBar.classList.add('bg-success');
                        } else if (hpPercentage > 20) {
                            hpBar.classList.add('bg-warning');
                        } else {
                            hpBar.classList.add('bg-danger');
                        }
                    }
                    if (hpText) {
                        hpText.textContent = `${hpPercentage}%`;
                    }
                    if (img) {
                        if (hpPercentage === 0) {
                            img.classList.add('grayscale');
                        } else {
                            img.classList.remove('grayscale');
                        }
                    }
                };

                hpBarContainer.addEventListener('mousedown', (e) => {
                    this.activeDragBar = hpBarContainer;
                    this.updateHpDisplayCallback = updateHpDisplay;
                    
                    const rect = this.activeDragBar.getBoundingClientRect();
                    let newWidth = e.clientX - rect.left;
                    let percentage = Math.round((newWidth / rect.width) * 100);
                    percentage = Math.max(0, Math.min(100, percentage));
                    this.updateHpDisplayCallback(percentage);
                });
            }
        });
    }

    async handlePredict() {
        const opponentPartyInputs = document.querySelectorAll('#opponent-party-form input');
        const resultArea = document.getElementById('prediction-result-area');

        const opponent_party = Array.from(opponentPartyInputs)
            .map(input => input.value)
            .filter(p => p.trim() !== '');

        let requestBody = { opponent_party };
        const selectedPartyId = this.myPartySelect.value;

        if (selectedPartyId) {
            requestBody.my_party_id = selectedPartyId;
        } else {
            const myPartyInputs = document.querySelectorAll('#my-party-form input');
            const my_party = Array.from(myPartyInputs)
                .map(input => input.value)
                .filter(p => p.trim() !== '');
            
            if (my_party.length !== 6) {
                alert('自分のパーティを6体入力するか、登録済みパーティを読み込んでください。');
                return;
            }
            requestBody.my_party = my_party;
        }

        if (opponent_party.length !== 6) {
            alert('相手のパーティをそれぞれ6体ずつ入力してください。');
            return;
        }

        setButtonLoading(this.predictButton, true);

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
            });

            const data = await response.json();

            if (response.ok) {
                this.displayPredictionResult(data, resultArea);
                // 選出アドバイスのタブをアクティブにする
                const selectionTab = new bootstrap.Tab(document.getElementById('selection-advice-tab'));
                selectionTab.show();
            } else {
                resultArea.innerHTML = `<div class="alert alert-danger">エラー: ${data.error || '不明なエラー'}</div>`;
            }
        } catch (error) {
            console.error('選出予測APIの呼び出し中にエラーが発生しました:', error);
            resultArea.innerHTML = `<div class="alert alert-danger">APIの呼び出しに失敗しました。</div>`;
        } finally {
            setButtonLoading(this.predictButton, false);
        }
    }

    displayPredictionResult(data, container) {
        let html = '<h5 class="neon-text-purple"><i class="bi bi-stars"></i> AI推奨選出</h5>';
        html += '<div class="row g-3 text-center">';
        data.recommended_team.forEach(name => {
            html += `
                <div class="col-4">
                    <div class="glass-card-inside p-3">
                        <div class="fw-bold fs-5">${escapeHTML(name)}</div>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        html += '<h5 class="mt-4 neon-text-purple"><i class="bi bi-lightbulb"></i> 選出理由</h5>';
        html += `<div class="glass-card-inside p-3"><p class="text-muted mb-0">${escapeHTML(data.reason)}</p></div>`;

        container.innerHTML = html;
    }
}