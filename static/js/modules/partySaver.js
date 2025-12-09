export class PartySaver {
    constructor(battleStateManager,pokemonDetailEditor) {
        this.battleStateManager = battleStateManager;
        this.pokemonDetailEditor = this.pokemonDetailEditor;
        this.alertContainer = document.querySelector('.container-fluid');
    }

    gatherBattleData() {
        const myPartySelect = document.getElementById('my-party-select');
        const myPartyId = myPartySelect.value;
        const detailedStates = this.battleStateManager.getBattleState();

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
                
                const itemEl = slot.querySelector('.item-name');
                const item = itemEl ? itemEl.textContent.trim() : '';

                const teraTypeSelect = slot.querySelector('.tera-type-name');
                const teraTypeId = teraTypeSelect ? teraTypeSelect.value : null;

                const abilityId = detailedState ? detailedState.ability_id : null;
                const moveIds = detailedState ? detailedState.moves.map(m => m.id).filter(id => id !== null) : [];

                return {
                    pokemon_name: name,
                    is_selected: isSelected,
                    is_first: isStarter,
                    item,
                    terastal_type: teraTypeId,
                    ability: abilityId,
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

        // ログバッファとBattleStateを取得してペイロードに追加
        if (this.realtimeAnalysis) {
            data.battle_state = this.battleStateManager.getBattleState();
        } else {
            data.battle_state = null;
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
                    const pokemonInput = slot.querySelector('.pokemon-input');
                    if (pokemonInput) {
                        pokemonInput.value = '';
                        pokemonInput.dispatchEvent(new Event('change', { bubbles: true })); // アイコンと種族値更新のため
                    }

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