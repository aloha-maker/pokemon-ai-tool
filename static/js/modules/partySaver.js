export class PartySaver {
    constructor(realtimeAnalysis) {
        this.realtimeAnalysis = realtimeAnalysis; // インスタンスを保持
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

        const opponentPartyInputs = document.querySelectorAll('#opponent-party-display .pokemon-input');
        const opponentParty = Array.from(opponentPartyInputs)
            .map(input => input.value.trim())
            .filter(name => name !== '');

        return {
            my_party_id: myPartyId,
            opponent_party: opponentParty
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

            if (response.ok) {
                this.showAlert(`対戦結果 (ID: ${responseData.log_id}) を保存しました。`, 'success');
                console.log('Success:', responseData);
            } else {
                throw new Error(responseData.error || '不明なエラーが発生しました。');
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