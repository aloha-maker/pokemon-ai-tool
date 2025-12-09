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

    async init() {
        await this.loadMasterData();
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

    async loadMasterData() {
        try {
            const response = await fetch('/api/master/items');
            if (!response.ok) throw new Error('持ち物マスターの取得に失敗しました。');
            this.items = await response.json();
        } catch (error) {
            console.error(error);
            // エラーが発生しても他の機能は続行させる
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
            const responseData = await response.json();

            if (responseData.status !== 'success') {
                throw new Error(responseData.message || 'パーティ一覧の取得に失敗しました。');
            }
            const parties = responseData.data;
            
            this.myPartySelect.innerHTML = '<option selected value="">登録済みパーティから選ぶ...</option>';
            parties.forEach(party => {
                const option = document.createElement('option');
                option.value = party.party_id;
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
            const responseData = await response.json();

            if (responseData.status !== 'success') {
                throw new Error(responseData.message || 'パーティ情報の取得に失敗しました。');
            }
            const party = responseData.data;

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
                    slot.querySelector('.pokemon-input').value = member.name || '';

                    // アイコンを更新　TODO ヘルパークラスでできる
                    const img = slot.querySelector('img');
                    if (img) {
                        const pokemonName = member.name;
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
                    
                    const itemInput = slot.querySelector('.item-input');
                    if (itemInput) {
                        itemInput.value = member.item || ''; // TODO IDから変換
                        // アイコン更新のためにchangeイベントを発火
                        itemInput.dispatchEvent(new Event('change'));
                    }

                    const teraSelect = slot.querySelector('.tera-type-select');
                    if (teraSelect) {
                        teraSelect.value = member.tera_type || ''; // TODO nullになっているので処理確認
                        teraSelect.dispatchEvent(new Event('change')); // To update icon
                    }
                }
            });

            // Dispatch event for other modules to update their state
            const event = new CustomEvent('partyLoaded', { detail: party.members });
            document.dispatchEvent(event);
            this.updateActivePokemonSelectors(); // 追加: activeポケモンセレクタを更新

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
                    this.updateActivePokemonSelectors(); // 追加: activeポケモンセレクタを更新

                };

                pokemonInput.addEventListener('change', updateIcon);    

                // 初期値がある場合に備えて、イベントを発火
                if (pokemonInput.value) {
                    updateIcon();
                }
            }

            // 持ち物入力イベントでアイコンを更新
            const itemInput = slot.querySelector('.item-input');
            const itemIcon = slot.querySelector('.item-icon');
            if (itemInput && itemIcon) {
                const updateItemIcon = () => {
                    const itemName = itemInput.value.trim();
                    if (itemName) {
                        itemIcon.src = `/static/item_icons/${itemName}.png`;
                        itemIcon.onerror = () => {
                            itemIcon.src = `https://placehold.co/24x24/333/ccc?text=?`;
                            itemIcon.onerror = null;
                        };

                    } else {
                        itemIcon.src = `https://placehold.co/24x24/333/ccc?text=?`;
                    }
                };

                itemInput.addEventListener('change', updateItemIcon);

                // 初期値がある場合に備えてイベントを発火
                if (itemInput.value) {
                    updateItemIcon();
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

        this.updateActivePokemonSelectors(); // 初期表示時にも更新
    }

    updateActivePokemonSelectors() {
        const myActiveSelect = document.getElementById('my-active-pokemon');
        const opponentActiveSelect = document.getElementById('opponent-active-pokemon');

        // セレクタをクリア
        myActiveSelect.innerHTML = '<option value="">選択なし</option>';
        opponentActiveSelect.innerHTML = '<option value="">選択なし</option>';

        // 自分のパーティのポケモンを取得して追加
        const myPartyInputs = document.querySelectorAll('#my-party-display .pokemon-input');

        myPartyInputs.forEach(input => {
            const pokemonName = input.value.trim();

            if (pokemonName) {
                const option = document.createElement('option');
                option.value = pokemonName;
                option.textContent = pokemonName;
                myActiveSelect.appendChild(option);
            }

        });

        // 相手のパーティのポケモンを取得して追加
        const opponentPartyInputs = document.querySelectorAll('#opponent-party-display .pokemon-input');

        opponentPartyInputs.forEach(input => {
            const pokemonName = input.value.trim();
            if (pokemonName) {
                const option = document.createElement('option');
                option.value = pokemonName;
                option.textContent = pokemonName;
                opponentActiveSelect.appendChild(option);
            }
        });

    }

    async handlePredict() {
        const opponentPartyInputs = document.querySelectorAll('#opponent-party-display .pokemon-input');
        const resultArea = document.getElementById('prediction-result-area');

        // TODO:相手パーティのポケモンIDを取得するようにする
        const opponent_party = Array.from(opponentPartyInputs)
            .map(input => input.value)
            .filter(p => p.trim() !== '');

        let requestBody = { opponent_party };

        // TODO:自分パーティのポケモンIDを取得するようにする
        const myPartyInputs = document.querySelectorAll('#my-party-display .pokemon-input');
        const my_party = Array.from(myPartyInputs)
            .map(input => input.value)
            .filter(p => p.trim() !== '');
        
        if (my_party.length !== 6) {
            alert('自分のパーティを6体入力するか、登録済みパーティを読み込んでください。');
            return;
        }
        requestBody.my_party = my_party;

        if (opponent_party.length !== 6) {
            alert('相手のパーティをそれぞれ6体ずつ入力してください。');
            return;
        }

        setButtonLoading(this.predictButton, true);

        try {
            const response = await fetch('/api/ai/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody),
            });

            const jsonResponse = await response.json();

            if (!response.ok || jsonResponse.status !== 'success') {
                const errorInfo = (jsonResponse.data && jsonResponse.data.error) || jsonResponse.message || '不明なエラー';
                throw new Error(errorInfo);
            }

            this.displayPredictionResult(jsonResponse.data, resultArea);
            // 選出アドバイスのタブをアクティブにする
            const selectionTab = new bootstrap.Tab(document.getElementById('selection-advice-tab'));
            selectionTab.show();

        } catch (error) {
            console.error('選出予測APIの呼び出し中にエラーが発生しました:', error);
            resultArea.innerHTML = `<div class="alert alert-danger">エラー: ${error.message}</div>`;
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

    displayDamageCalculations(damageData) {
        const myToOpponentContainer = document.getElementById('self-to-opponent-damage-cards');
        const opponentToMyContainer = document.getElementById('opponent-to-self-damage-cards');

        if (!myToOpponentContainer || !opponentToMyContainer) {
            console.error('Damage calculation containers not found.');
            return;
        }

        const createDamageCardsHtml = (damageDict) => {
            if (!damageDict || Object.keys(damageDict).length === 0) {
                return '<p class="text-white-50 small">計算データがありません。</p>';
            }

            let html = '';
            for (const [moveName, defendersData] of Object.entries(damageDict)) {
                for (const [defenderName, calc] of Object.entries(defendersData)) {
                    const minPercent = calc.percent_min;
                    const maxPercent = calc.percent_max;

                    let hitsToKO = '---';
                    if (minPercent > 0) {
                        const hits = Math.ceil(100 / minPercent);
                        if (hits === 1) {
                            hitsToKO = '確定1発';
                        } else if (hits <= 4) {
                            hitsToKO = `確定${hits}発`;
                        } else {
                            const randomHits = Math.ceil(100 / maxPercent);
                            if (randomHits > 0 && randomHits <= 4) {
                                hitsToKO = `乱数${randomHits}発`;
                            }
                        }
                    }

                    let effectivenessBadge = '';
                    if (calc.effectiveness > 1) {
                        effectivenessBadge = `<span class="badge bg-success-subtle text-success-emphasis rounded-pill">ばつぐん</span>`;
                    } else if (calc.effectiveness < 1 && calc.effectiveness > 0) {
                        effectivenessBadge = `<span class="badge bg-danger-subtle text-danger-emphasis rounded-pill">いまひとつ</span>`;
                    } else if (calc.effectiveness === 0) {
                        effectivenessBadge = `<span class="badge bg-secondary-subtle text-secondary-emphasis rounded-pill">効果なし</span>`;
                    }

                    html += `
                        <div class="card glass-card-sm mb-2">
                            <div class="card-body p-2">
                                <h6 class="card-title text-white mb-1">${escapeHTML(moveName)} (${escapeHTML(defenderName)})</h6>
                                <p class="card-text mb-1">${minPercent}% ~ ${maxPercent}% (${hitsToKO})</p>
                                ${effectivenessBadge}
                            </div>
                        </div>
                    `;
                }
            }
            return html;
        };
        
        // 自分 -> 相手
        myToOpponentContainer.innerHTML = '<h6 class="text-white mb-2">自分 → 相手</h6>';
        if (damageData && damageData.my_to_opponent) {
            myToOpponentContainer.innerHTML += createDamageCardsHtml(damageData.my_to_opponent);
        } else {
            myToOpponentContainer.innerHTML += '<p class="text-white-50 small">計算データがありません。</p>';
        }

        // 相手 -> 自分
        opponentToMyContainer.innerHTML = '<h6 class="text-white mb-2">相手 → 自分</h6>';
        if (damageData && damageData.opponent_to_my) {
            opponentToMyContainer.innerHTML += createDamageCardsHtml(damageData.opponent_to_my);
        } else {
            opponentToMyContainer.innerHTML += '<p class="text-white-50 small">計算データがありません。</p>';
        }

        // 戦況分析タブをアクティブにする
        const analysisTab = document.getElementById('battle-analysis-tab');
        if (analysisTab) {
            const tab = new bootstrap.Tab(analysisTab);
            tab.show();
        }
    }
}