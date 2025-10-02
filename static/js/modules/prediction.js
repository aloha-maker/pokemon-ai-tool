// prediction.js - 選出予測機能

import { escapeHTML, setButtonLoading } from './utils.js';

export class PredictionManager {
    constructor() {
        this.predictButton = document.getElementById('predict-button');
        this.myPartySelect = document.getElementById('my-party-select');
        this.loadMyPartyBtn = document.getElementById('load-my-party-btn');
        this.myPartyDisplay = document.getElementById('my-party-display');
        this.items = []; // 持ち物リストを保持
        
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
            this.initPartyDisplay();
        }
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
            const myPartyInputs = document.querySelectorAll('#my-party-display .pokemon-input');
            myPartyInputs.forEach(input => input.value = '');

            party.members.forEach((member, index) => {
                if (index < myPartyInputs.length) {
                    myPartyInputs[index].value = member.pokemon_name;
                    // TODO: HPや持ち物もここで設定する
                }
            });

        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }

    initPartyDisplay() {
        const pokemonSlots = this.myPartyDisplay.querySelectorAll('.pokemon-slot');

        pokemonSlots.forEach(slot => {
            const img = slot.querySelector('img');
            const hpBarContainer = slot.querySelector('.hp-bar-container');
            const hpBar = slot.querySelector('.hp-bar');
            const hpText = slot.querySelector('.hp-text');
            const starterIcon = slot.querySelector('.starter-icon');
            const itemIcon = slot.querySelector('.item-icon');
            const itemSelect = slot.querySelector('.item-select');

            // --- 1. 選出/先発のクリック処理 ---
            img.dataset.clickState = '0';
            img.addEventListener('click', () => {
                const currentState = parseInt(img.dataset.clickState, 10);
                let nextState;

                if (currentState === 0) { // 未選択 -> 選択
                    nextState = 1;
                    img.classList.add('pokemon-selected');
                    starterIcon.classList.add('d-none');
                } else if (currentState === 1) { // 選択 -> 選択+先発
                    nextState = 2;
                    img.classList.add('pokemon-selected');
                    starterIcon.classList.remove('d-none');
                } else { // 選択+先発 -> 未選択
                    nextState = 0;
                    img.classList.remove('pokemon-selected');
                    starterIcon.classList.add('d-none');
                }
                img.dataset.clickState = nextState.toString();
            });

            // --- 2. HPバーのドラッグ処理 ---
            let isDragging = false;
            const updateHpDisplay = (hpPercentage) => {
                hpBar.style.width = `${hpPercentage}%`;
                hpBar.setAttribute('aria-valuenow', hpPercentage);
                hpText.textContent = `${hpPercentage}%`;
                hpBar.classList.remove('bg-success', 'bg-warning', 'bg-danger');
                if (hpPercentage > 50) {
                    hpBar.classList.add('bg-success');
                } else if (hpPercentage > 20) {
                    hpBar.classList.add('bg-warning');
                } else {
                    hpBar.classList.add('bg-danger');
                }
                img.classList.toggle('grayscale', hpPercentage === 0);
            };

            const onDrag = (e) => {
                const rect = hpBarContainer.getBoundingClientRect();
                let newWidth = e.clientX - rect.left;
                let percentage = Math.round((newWidth / rect.width) * 100);
                percentage = Math.max(0, Math.min(100, percentage));
                updateHpDisplay(percentage);
            };

            hpBarContainer.addEventListener('mousedown', (e) => { isDragging = true; onDrag(e); });
            document.addEventListener('mousemove', (e) => { if (isDragging) { onDrag(e); } });
            document.addEventListener('mouseup', () => { isDragging = false; });

            // --- 3. 持ち物選択処理 ---
            // プルダウンを生成
            this.items.forEach(item => {
                const option = document.createElement('option');
                option.value = item.id;
                option.textContent = item.name_ja;
                itemSelect.appendChild(option);
            });

            // アイコンクリックでプルダウン表示
            itemIcon.addEventListener('click', () => {
                itemIcon.classList.add('d-none');
                itemSelect.classList.remove('d-none');
                itemSelect.focus();
            });

            const hideSelect = () => {
                itemSelect.classList.add('d-none');
                itemIcon.classList.remove('d-none');
            };

            // プルダウン変更で値を保存し、表示を戻す
            itemSelect.addEventListener('change', () => {
                const selectedOption = itemSelect.options[itemSelect.selectedIndex];
                slot.dataset.selectedItemId = itemSelect.value;
                slot.dataset.selectedItemName = selectedOption.textContent;
                
                // TODO: アイコン画像を動的に変更する
                // if (itemSelect.value) {
                //     itemIcon.src = `/static/images/items/${selectedOption.textContent}.png`;
                // } else {
                //     itemIcon.src = 'https://placehold.co/24x24/777/eee?text=?';
                // }

                hideSelect();
            });

            // フォーカスが外れたら表示を戻す
            itemSelect.addEventListener('blur', () => {
                hideSelect();
            });
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
