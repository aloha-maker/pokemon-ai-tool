export class PartySaver {
    constructor(realtimeAnalysis, pokemonDetailEditor) {
        this.realtimeAnalysis = realtimeAnalysis; // インスタンスを保持
        this.pokemonDetailEditor = pokemonDetailEditor; // インスタンスを保持
        this.savePartyBtn = document.getElementById('save-party-button');
        this.resultModalEl = document.getElementById('result-modal');
        this.resultModal = this.resultModalEl ? new bootstrap.Modal(this.resultModalEl) : null;
        this.resultButtons = document.querySelectorAll('#result-modal [data-result]');
        this.alertContainer = document.querySelector('.container-fluid');

        if (this.savePartyBtn && this.resultModal) {
            this.init();
        }
    }

    init() {
        this.savePartyBtn.addEventListener('click', () => {
            // 先にパーティ情報が入力されているかチェック
            const data = this.gatherBattleData();
            if (!data.my_party_id) {
                this.showAlert('自パーティが選択されていません。', 'warning');
                return;
            }
            if (data.opponent_party.length === 0) {
                this.showAlert('相手パーティが入力されていません。', 'warning');
                return;
            }
            // 問題なければモーダル表示
            this.resultModal.show();
        });

        this.resultButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const result = e.currentTarget.dataset.result; // 'win' or 'lose'
                this.saveBattleResult(result);
                this.resultModal.hide();
            });
        });
    }

    gatherBattleData() {
        const myPartySelect = document.getElementById('my-party-select');
        const myPartyId = myPartySelect.value;
        const detailedStates = this.pokemonDetailEditor.getState();

        const processParty = (containerSelector, partyIndexOffset) => {
            const slots = document.querySelectorAll(`${containerSelector} .pokemon-slot`);
            return Array.from(slots).map((slot, index) => {
                const slotIndex = partyIndexOffset + index;
                const detailedState = detailedStates[slotIndex];

                const nameEl = slot.querySelector('.pokemon-input');
                const name = nameEl ? nameEl.value.trim() : '';

                const starterIcon = slot.querySelector('.starter-icon');
                const isStarter = starterIcon ? !starterIcon.classList.contains('d-none') : false;

                const imgEl = slot.querySelector('img');
                const isSelected = isStarter || (imgEl ? imgEl.classList.contains('pokemon-selected') : false);
                
                const itemEl = slot.querySelector('.item-input');
                const item = itemEl ? itemEl.value.trim() : '';

                const teraTypeSelect = slot.querySelector('.tera-type-select');
                const teraTypeId = teraTypeSelect ? teraTypeSelect.value : null;

                const abilityId = detailedState ? detailedState.ability_id : null;
                const moveIds = detailedState ? detailedState.moves.map(m => m.id).filter(id => id !== null) : [];

                return {
                    name,
                    is_selected: isSelected,
                    is_starter: isStarter,
                    item,
                    terastal_type_id: teraTypeId,
                    ability_id: abilityId,
                    moves: moveIds
                };
            }).filter(p => p.name !== '');
        };

        const myParty = processParty('#my-party-display', 0);
        const opponentParty = processParty('#opponent-party-display', 6);
        
        const battleIdDisplay = document.getElementById('battle-id-display');
        const battleId = battleIdDisplay ? battleIdDisplay.value : null;

        return {
            my_party_id: myPartyId,
            my_party: myParty,
            opponent_party: opponentParty,
            battle_id: battleId
        };
    }

    async saveBattleResult(result) {
        const data = this.gatherBattleData();
        data.result = result; // 'win' or 'lose'

        // ログバッファを取得してペイロードに追加
        if (this.realtimeAnalysis) {
            data.raw_events = this.realtimeAnalysis.getLogBuffer();
        } else {
            data.raw_events = [];
        }

        try {
            const response = await fetch('/api/battles/save_result_with_log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const responseData = await response.json();

            if (response.ok && responseData.status === 'success') {
                this.showAlert(`対戦結果 (ID: ${responseData.data.log_id}) を保存しました。`, 'success');
                console.log('Success:', responseData);

                // 新しいバトルIDを採番して表示
                if (this.realtimeAnalysis) {
                    await this.realtimeAnalysis.fetchAndSetNewBattleId();
                }

                // 相手パーティの入力情報をクリア
                document.querySelectorAll('#opponent-party-display .pokemon-slot').forEach(slot => {
                    // ポケモン名
                    slot.querySelector('.pokemon-input').value = '';

                    // 持ち物
                    const itemInput = slot.querySelector('.item-input');
                    if (itemInput) {
                        itemInput.value = '';
                        itemInput.dispatchEvent(new Event('input')); // アイコン更新のため
                    }

                    // テラスタイプ
                    const teraSelect = slot.querySelector('.tera-type-select');
                    if (teraSelect) {
                        teraSelect.selectedIndex = 0;
                        teraSelect.dispatchEvent(new Event('change')); // アイコン更新のため
                    }
                });

                // 自分と相手のパーティの選出フラグ（星と青枠）をクリア
                document.querySelectorAll('#my-party-display .pokemon-slot, #opponent-party-display .pokemon-slot').forEach(slot => {
                    // スターターアイコン（星）を非表示に
                    const starterIcon = slot.querySelector('.starter-icon');
                    if (starterIcon) {
                        starterIcon.classList.add('d-none');
                    }
                    // 選出ポケモン（青枠）を解除
                    const pokemonImage = slot.querySelector('.pokemon-image');
                    if (pokemonImage) {
                        pokemonImage.classList.remove('pokemon-selected');
                    }
                });

                // 相手パーティの詳細情報（特性・技）をクリア
                if (this.pokemonDetailEditor) {
                    this.pokemonDetailEditor.clearOpponentDetails();
                }
            } else {
                const errorMessage = responseData.data ? responseData.data.error : (responseData.message || '不明なエラーが発生しました。');
                throw new Error(errorMessage);
            }
        } catch (error) {
            console.error('Error:', error);
            this.showAlert(`エラー: ${error.message}`, 'danger');
        }
    }

    showAlert(message, type) {
        const existingAlert = this.alertContainer.querySelector('.dynamic-alert');
        if (existingAlert) {
            existingAlert.remove();
        }

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show dynamic-alert`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '2000';

        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        this.alertContainer.prepend(alertDiv);

        setTimeout(() => {
            const bootstrapAlert = bootstrap.Alert.getOrCreateInstance(alertDiv);
            if (bootstrapAlert) {
                bootstrapAlert.close();
            }
        }, 5000);
    }
}