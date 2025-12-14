import { escapeHTML } from './utils.js';

export class RealtimeAnalysis {
    constructor(battleStateManager,predictionManager) {
        this.socket = io("http://localhost:8000");
        this.battleStateManager = battleStateManager;
        this.predictionManager = predictionManager;
        this.captureImage = document.getElementById('capture-image');
        this.recognizePartyBtn = document.getElementById('recognize-opponent-party-btn');
        this.confirmSelectionBtn = document.getElementById('confirm-selection-btn');
        this.completeSelectionBtn = document.getElementById('complete-selection-btn');
        this.logOutput = document.getElementById('realtime-log-output');
        this.startCameraBtn = document.getElementById('start-camera-btn');
        this.startBattleBtn = document.getElementById('start-battle-btn');
        this.battleIdDisplay = document.getElementById('battle-id-display');
        this.logBuffer = [];
        this.sequence = 0;
        this.partySaver = null;
        
        this.init();
    }

    init() {
        this.setUIState('stopped');
        this.initSocketListeners();
        
        this.recognizePartyBtn?.addEventListener('click', () => this.handleRecognizeParty());
        this.confirmSelectionBtn?.addEventListener('click', () => this.handleConfirmSelection());
        this.completeSelectionBtn?.addEventListener('click', () => this.handleConfirmSelection());
        this.startCameraBtn?.addEventListener('click', () => this.handleStartCamera());
        this.startBattleBtn?.addEventListener('click', () => this.handleStartBattle());
    }

    setPartySaver(partySaver) {
        this.partySaver = partySaver;
    }

    initSocketListeners() {
        this.socket.on('connect', () => {
            console.log('WebSocket connected!');
        });

        // パーティ取得ボタン押下
        this.socket.on('camera_started', (data) => {
            console.log('Camera stream started by server.');
            this.setUIState('running_camera');
            if (data.video_feed_url) {
                this.captureImage.src = data.video_feed_url;
            }
        });

        this.socket.on('ocr_started', () => {
            console.log('OCR started by server.');
            this.setUIState('running_camera_ocr');
        });

        this.socket.on('analysis_stopped', (data) => {
            console.log('Analysis stopped by server.');
            if (data && data.error) {
                alert(`解析が停止しました: ${data.error}`);
            }
            this.setUIState('stopped');
            this.captureImage.src = "https://placehold.co/1280x720/0c0a24/e5bfff?text=Game+Capture+Preview";
        });

        this.socket.on('ocr_update', async (data) => {
            const latest_events = data.latest_events;
            if (this.logOutput && latest_events) {
                this.appendRealtimeLog(latest_events);
                // サーバーから battle_state が送られてきたらUIを更新する
                if (data.battle_state) {
                    console.log("Received battle state, updating UI.", data.battle_state);
                    this.updateUIWithBattleState(data.battle_state);
                }
            }

            const phase = data.phase_info['current_phase']
            const sub_phase = data.phase_info['battle_sub_phase']

            // フェーズとサブフェーズのUIを更新
            const phaseDisplay = document.getElementById('phase-display');
            const subPhaseDisplay = document.getElementById('sub-phase-display');
            phaseDisplay.value = phase || '';
            subPhaseDisplay.value = sub_phase || '';

            console.log('phase',phase)
            console.log('sub_phase',sub_phase)

            if(phase === 'stay') {
                // パーティ取得,選出完了,選択完了ボタン　非活性
                this.recognizePartyBtn.disabled = true;
                this.confirmSelectionBtn.disabled = true;
                this.completeSelectionBtn.disabled = true;
            }else if(phase === 'select'){
                // パーティ取得,選出完了ボタン　活性
                this.recognizePartyBtn.disabled = false;
                this.confirmSelectionBtn.disabled = false;
                this.handleRecognizeParty()
            }else if(phase === 'battle'){
                // パーティ取得,選出完了ボタン　非活性
                this.recognizePartyBtn.disabled = true;
                this.confirmSelectionBtn.disabled = true;
                if(sub_phase === 'choose'){
                    // 選択完了ボタン　活性
                    this.completeSelectionBtn.disabled = false;
                    const battleState = this.battleStateManager.getBattleState();

                    const response = await fetch('/api/ai/get_suggestion', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(battleState),
                    });
                    
                    const jsonResponse = await response.json();
                    console.log('Suggestion received:', jsonResponse); // サーバー内部で予期せぬエラーが発生しました。
                    this.displaySuggestion(jsonResponse.recommendation);

                    if (this.predictionManager && jsonResponse.damage_calcs) {
                        this.predictionManager.displayDamageCalculations(jsonResponse.damage_calcs);
                    }
                }else if(sub_phase === 'act'){
                    // 選択完了ボタン　非活性
                    this.completeSelectionBtn.disabled = true;
                }
            }

            // バトルが終わったらログ情報をDBに保存
            // バトル終了判定条件を TODO act → stayに変更
            if(data.result !== 'unknown'){
                console.log(data.result,'バトルログを保存します。')
                this.partySaver.saveBattleResult(data.result)
                this.handleStartBattle()
                await this.fetchAndSetNewBattleId();
                const battleState = this.battleStateManager.getBattleState();
                this.socket.emit('start_ocr', battleState, this.battleIdDisplay.value);
                this.resetResultArea();
            }
        });

        this.socket.on('suggestion_update', (data) => {
            console.log('Suggestion received:', data);
            this.displaySuggestion(data);
        });
    }

    resetResultArea() {
        const resultArea = document.getElementById('prediction-result-area');
        resultArea.innerHTML = `
            <div class="text-center pt-5 h-100">
                <button id="predict-button" class="btn btn-lg btn-primary neon-border">
                    <span class="spinner-border spinner-border-sm d-none" role="status"
                        aria-hidden="true"></span>
                    予測を開始
                </button>
            </div>
        `;
        
        // ボタンの参照を再取得して、イベントリスナーを再設定する必要があります
        this.predictButton = document.getElementById('predict-button');
        // 必要に応じてイベントリスナーを再アタッチ
        this.predictButton.addEventListener('click', () => this.predictionManager.handlePredict());
    }

    appendRealtimeLog(latest_events) {
        const logEntry = document.createElement('div');
        logEntry.classList.add('log-entry', 'mb-2', 'pb-1', 'border-bottom', 'border-secondary', 'border-opacity-25');
        const timestamp = new Date().toLocaleTimeString();
        let content = `<div class="text-muted small">[${timestamp}]</div>`;
        const rawResult = latest_events;
        let hasContent = false;
        if (rawResult && typeof rawResult === 'object' && Object.keys(rawResult).length > 0) {
            content += '<ul class="list-unstyled mb-0 small">';
            for (const [key, value] of Object.entries(rawResult)) {
                const text = value.text;
                if (text && String(text).trim()) {
                    content += `<li><span class="text-info" style="min-width: 180px; display: inline-block;">${escapeHTML(key)}:</span> <strong>${escapeHTML(text)}</strong></li>`;
                    hasContent = true;
                }
            }
            content += '</ul>';
        }
        if (hasContent) {
            logEntry.innerHTML = content;
            this.logOutput.prepend(logEntry);
        }
        if (this.logOutput.children.length > 50) {
            this.logOutput.removeChild(this.logOutput.lastChild);
        }
        if (hasContent) {
            for (const [key, value] of Object.entries(rawResult)) {
                if (value && String(value).trim()) {
                    this.logBuffer.push({ sequence: this.sequence, roi_name: key, ocr_text: value });
                }
            }
            this.sequence++;
        }
    }

    setUIState(state) {
        this.currentState = state;
        const cameraBtn = this.startCameraBtn;
        const battleBtn = this.startBattleBtn;
        if (cameraBtn) cameraBtn.disabled = false;
        if (battleBtn) battleBtn.disabled = true;
        if (this.recognizePartyBtn) this.recognizePartyBtn.disabled = true;
        if (cameraBtn) {
            cameraBtn.innerHTML = '<i class="bi bi-camera-video-fill"></i> 仮想カメラ読込';
            cameraBtn.classList.remove('btn-danger');
            cameraBtn.classList.add('btn-info');
        }
        if (state === 'stopped') {
        } else if (state === 'running_camera') {
            if (cameraBtn) {
                cameraBtn.innerHTML = '<i class="bi bi-stop-circle-fill"></i> 停止';
                cameraBtn.classList.add('btn-danger');
            }
            if (battleBtn) battleBtn.disabled = false;
            if (this.recognizePartyBtn) this.recognizePartyBtn.disabled = false;
        } else if (state === 'running_camera_ocr') {
            if (cameraBtn) {
                cameraBtn.innerHTML = '<i class="bi bi-stop-circle-fill"></i> 停止';
                cameraBtn.classList.add('btn-danger');
            }
            if (battleBtn) battleBtn.disabled = true;
            if (this.recognizePartyBtn) this.recognizePartyBtn.disabled = false;
        }
    }

    handleStartCamera() {
        console.log("handleStartCamera called!");
        const cameraIndex = document.getElementById('camera-index-input').value || 0;
        if (this.currentState === 'running_camera' || this.currentState === 'running_camera_ocr') {
            this.socket.emit('stop_analysis', {});
        } else {
            this.clearLogs();
            console.log(`Attempting to emit start_camera with index: ${cameraIndex}`);
            this.socket.emit('start_camera', { camera_index: parseInt(cameraIndex, 10) });
        }
    }

    handleStartOcr() {
        if (this.currentState === 'running_camera') {
            const battleState = this.battleStateManager.getBattleState();
            const battleId = this.battleIdDisplay ? this.battleIdDisplay.value : null; // バトルIDを取得

            console.log("Sending battle state to server on OCR start:", battleState, "with Battle ID:", battleId);
            this.socket.emit('start_ocr', battleState, battleId);
        }
    }

    handleConfirmSelection() {
        if (this.currentState === 'running_camera_ocr') {
            const battleState = this.battleStateManager.getBattleState();
            console.log('battleState',battleState)
            this.socket.emit('resume_ocr', battleState);
        }
    }

    async handleStartBattle() {
        this.handleStartOcr();
        await this.fetchAndSetNewBattleId();
    }

    async fetchAndSetNewBattleId() {
        try {
            const response = await fetch('/api/battle/new_id');
            if (!response.ok) {
                throw new Error('サーバーからバトルIDを取得できませんでした。');
            }
            const result = await response.json();
            if (result.status === 'success' && result.data.battle_id) {
                if (this.battleIdDisplay) {
                    this.battleIdDisplay.value = result.data.battle_id;
                    this.battleIdDisplay.dispatchEvent(new Event('input'));
                }
                console.log(`Fetched Battle ID: ${result.data.battle_id}`);
            } else {
                throw new Error('レスポンスにバトルIDが含まれていません。');
            }
        } catch (error) {
            console.error('バトルIDの取得に失敗しました:', error);
            if (this.battleIdDisplay) {
                this.battleIdDisplay.value = 'エラー';
                this.battleIdDisplay.dispatchEvent(new Event('input'));
            }
        }
    }

    clearLogs() {
        this.logBuffer = [];
        this.sequence = 0;
        if (this.logOutput) {
            this.logOutput.innerHTML = '';
        }
    }

    getLogBuffer() {
        return this.logBuffer;
    }

    displaySuggestion(data) {
        const suggestionContainer = document.getElementById('suggestion-overlay');
        if (data && data.action) {
            let html = `
                <div class="advice-card p-3 rounded-lg mb-4 glass-card-inside">
                    <h5 class="font-semibold text-md mb-3 neon-text-purple"><i class="bi bi-star-fill"></i> 推奨アクション</h5>
                    <div class="text-center">
                        <p class="lead mb-1">${escapeHTML(data.action)}</p>
                        <h2 class="display-6 fw-bold">${escapeHTML(data.target || '')}</h2>
                    </div>
                </div>
                <div class="advice-card p-3 rounded-lg glass-card-inside">
                    <h5 class="font-semibold text-md mb-2 neon-text-purple"><i class="bi bi-lightbulb-fill"></i> アドバイスの根拠</h5>
                    <p class="text-muted small mb-0">${escapeHTML(data.reason)}</p>
                </div>
            `;
            suggestionContainer.innerHTML = html;
            const battleTab = new bootstrap.Tab(document.getElementById('battle-advice-tab'));
            battleTab.show();
        } else {
            suggestionContainer.innerHTML = `
                <div class="text-center text-muted pt-5 h-100">
                    <p>現在、推奨できるアクションはありません。</p>
                </div>
            `;
        }
    }

    async handleRecognizeParty() {
        if (!this.recognizePartyBtn || this.recognizePartyBtn.disabled) return;
        const originalHtml = this.recognizePartyBtn.innerHTML;
        this.recognizePartyBtn.disabled = true;
        this.recognizePartyBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            認識中...
        `;
        try {
            const response = await fetch('/api/party/recognize_opponent', { method: 'POST' });
            const data = await response.json();
            console.log('Received data from API:', data);
            if (data.status === 'success' && data.data.party) {
                const opponentInputs = document.querySelectorAll('#opponent-party-display .pokemon-input');
                data.data.party.forEach((pokemonName, index) => {
                    if (opponentInputs[index]) {
                        opponentInputs[index].value = pokemonName || '';
                        opponentInputs[index].dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
                this.predictionManager.handlePredict();
            } else {
                const errorMessage = data.data ? data.data.error : (data.message || '不明なエラー');
                alert(`パーティの認識に失敗しました: ${errorMessage}`);
            }
        } catch (error) {
            console.error('パーティ認識APIの呼び出し中にエラーが発生しました:', error);
            alert('パーティの認識中にエラーが発生しました。');
        } finally {
            this.recognizePartyBtn.disabled = false;
            this.recognizePartyBtn.innerHTML = originalHtml;
        }
    }

    /**
     * サーバーから受信したBattleStateオブジェクトでUIを更新します。
     * 正確な階層構造を反映しています。
     * @param {object} battleState - サーバーから送信されたバトル状態オブジェクト。
     */
    updateUIWithBattleState(battleState) {

        if (!battleState) {
            console.warn("updateUIWithBattleState: battleState is null or undefined.");
            return;
        }

        // side1 (自分側) のデータを更新
        if (battleState.side1) {
            this.updateSideUI('my', battleState.side1);
        }

        // side2 (相手側) のデータを更新
        if (battleState.side2) {
            this.updateSideUI('opponent', battleState.side2);
        }

        // フィールドの状態を更新
        if (battleState.field) {
            this.updateFieldUI(battleState.field);
        }
    }

    /**
     * 片方のサイド（自分または相手）のUIを更新します。
     * @param {string} containerId - 'my-party' または 'opponent-party'。
     * @param {object} sideData - BattleSideのデータ。
     */
    // TODO UIの更新状況強の最新化
    updateSideUI(containerId, sideData) {
        const displayContainer = document.getElementById(containerId + '-party-display');

        // アクティブなポケモンのUIを更新
        if (sideData.active) {
            const pokemon = sideData.active;
            // ポケモン名
            document.getElementById(containerId + '-active-pokemon').value = pokemon.name
        }

        // パーティ全体の情報を詳細に更新
        if (sideData.team && Array.isArray(sideData.team.members)) {
            sideData.team.members.forEach((pokemon, index) => {
                // 各パーティメンバーのUIコンテナを取得 (HTML構造を仮定)
                // 例: <div class="party-member-container" data-pokemon-index="0"> ... </div>
                const memberContainer = displayContainer.querySelector(`.party-member-container[data-pokemon-index="${index}"]`);
                if (!memberContainer) return;

                // 1. ポケモンアイコンの更新 (瀕死状態など)
                const iconEl = memberContainer.querySelector('.party-pokemon-icon');
                if (iconEl) {
                    if (pokemon.current_hp === 0) {
                        iconEl.classList.add('fainted');
                    } else {
                        iconEl.classList.remove('fainted');
                    }
                }

                // 3. 状態異常アイコンの更新
                const statusIcon = memberContainer.querySelector('.party-status-icon');
                if (statusIcon) {
                    if (pokemon.status) {
                        statusIcon.src = `/static/ailment_icons/${pokemon.status}.png`;
                        statusIcon.title = pokemon.status;
                        statusIcon.style.display = 'inline';
                    } else {
                        statusIcon.style.display = 'none';
                    }
                }

                // 4. ポケモン名やHPテキストなど、その他の情報の更新 (必要に応じて)
                const nameEl = memberContainer.querySelector('.party-pokemon-name');
                if (nameEl) {
                    nameEl.textContent = pokemon.name;
                }
                const hpTextEl = memberContainer.querySelector('.party-hp-text');
                if (hpTextEl) {
                    hpTextEl.textContent = `${pokemon.current_hp}/${pokemon.max_hp}`;
                }
            });
        }
    }

    /**
     * バトルフィールド（天候など）のUIを更新します。
     * @param {object} fieldData - BattleFieldのデータ。
     */
    updateFieldUI(fieldData) {
        const weatherDisplay = document.getElementById('weather-display');
        if (weatherDisplay) {
            weatherDisplay.textContent = `天候: ${fieldData.weather || 'なし'}`;
        }

        const fieldEffectDisplay = document.getElementById('field-effect-display');
        if (fieldEffectDisplay) {
            fieldEffectDisplay.textContent = `フィールド: ${fieldData.terrain || 'なし'}`;
        }
    }
}