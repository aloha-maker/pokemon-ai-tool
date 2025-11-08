import { escapeHTML } from './utils.js';
import { createBattleState } from '../collectors/BattleState.js';
import { gatherSideDataAsJson } from '../collectors/pokemonDataCollector.js';

export class RealtimeAnalysis {
    constructor() {
        this.socket = io();
        this.captureImage = document.getElementById('capture-image');
        this.recognizePartyBtn = document.getElementById('recognize-opponent-party-btn');
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
        this.startCameraBtn?.addEventListener('click', () => this.handleStartCamera());
        this.startBattleBtn?.addEventListener('click', () => this.handleStartBattle());

        if (this.battleIdDisplay) {
            const savePartyBtn = document.getElementById('save-party-button');
            if (savePartyBtn) {
                savePartyBtn.disabled = !this.battleIdDisplay.value;
                this.battleIdDisplay.addEventListener('input', () => {
                    savePartyBtn.disabled = !this.battleIdDisplay.value;
                });
            }
        }
    }

    setPartySaver(partySaver) {
        this.partySaver = partySaver;
    }    

    initSocketListeners() {
        this.socket.on('connect', () => {
            console.log('WebSocket connected!');
        });

        this.socket.on('analysis_started', (data) => {
            console.log('Analysis started by server.');
            this.setUIState('running_window');
            if (data.video_feed_url) {
                this.captureImage.src = data.video_feed_url;
            }
        });

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

        this.socket.on('ocr_update', (data) => {
            const latest_events = data.latest_events;
            if (this.logOutput && latest_events) {
                this.appendRealtimeLog(latest_events);
                // サーバーから battle_state が送られてきたらUIを更新する
                if (data.battle_state) {
                    console.log("Received battle state, updating UI.", data.battle_state);
                    this.updateUIWithBattleState(data.battle_state);
                }
            }

            if(data.phase_info['current_phase'] === 'battle' && data.phase_info['battle_sub_phase'] === 'choose') {
                const battleState = this.gatherFullBattleState();
                console.log("Sending full battle state for suggestion:", battleState);
                this.socket.emit('get_suggestion', battleState);
            }
        });

        this.socket.on('suggestion_update', (data) => {
            console.log('Suggestion received:', data);
            this.displaySuggestion(data);
        });
    }

    gatherFullBattleState() {
        console.log("Gathering full battle state...");
        const side1Data = gatherSideDataAsJson('my-party');
        const side2Data = gatherSideDataAsJson('opponent-party');
        return createBattleState({ side1: side1Data, side2: side2Data });
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
            const battleState = this.gatherFullBattleState();
            const battleId = this.battleIdDisplay ? this.battleIdDisplay.value : null; // バトルIDを取得

            console.log("Sending battle state to server on OCR start:", battleState, "with Battle ID:", battleId);
            this.socket.emit('start_ocr', battleState, battleId);
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
            this.updateSideUI('my-party', battleState.side1);
        }

        // side2 (相手側) のデータを更新
        if (battleState.side2) {
            this.updateSideUI('opponent-party', battleState.side2);
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
    updateSideUI(containerId, sideData) {
        const displayContainer = document.getElementById(containerId + '-display');
        if (!displayContainer) {
            console.warn(`updateSideUI: Display container for #${containerId} not found.`);
            return;
        }

        // アクティブなポケモンのUIを更新 (この部分は変更なし)
        if (sideData.active) {
            const pokemon = sideData.active;
            const activePokemonContainer = displayContainer.querySelector('.active-pokemon-display');

            if (activePokemonContainer) {
                // ポケモン名
                const nameEl = activePokemonContainer.querySelector('.pokemon-name');
                if (nameEl) nameEl.textContent = pokemon.name || '---';

                // HPバー
                const hpBar = activePokemonContainer.querySelector('.hp-bar-inner');
                if (hpBar) {
                    const hpPercentage = (pokemon.max_hp > 0) ? (pokemon.current_hp / pokemon.max_hp) * 100 : 0;
                    hpBar.style.width = `${hpPercentage}%`;
                }

                // HPテキスト
                const hpText = activePokemonContainer.querySelector('.hp-text');
                if (hpText) hpText.textContent = (pokemon.current_hp !== null && pokemon.max_hp !== null) ? `${pokemon.current_hp} / ${pokemon.max_hp}` : 'HP';

                // 状態異常アイコン
                const statusIcon = activePokemonContainer.querySelector('.status-icon');
                if (statusIcon) {
                    if (pokemon.status) {
                        statusIcon.src = `/static/ailment_icons/${pokemon.status}.png`;
                        statusIcon.style.display = 'inline';
                        statusIcon.title = pokemon.status;
                    } else {
                        statusIcon.style.display = 'none';
                    }
                }
            }
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

                // 2. HPバーの更新
                const hpBar = memberContainer.querySelector('.party-hp-bar-inner');
                if (hpBar) {
                    const hpPercentage = (pokemon.max_hp > 0) ? (pokemon.current_hp / pokemon.max_hp) * 100 : 0;
                    hpBar.style.width = `${hpPercentage}%`;
                    
                    // HP残量に応じて色を更新
                    hpBar.classList.remove('hp-high', 'hp-medium', 'hp-low');
                    if (hpPercentage > 50) {
                        hpBar.classList.add('hp-high');
                    } else if (hpPercentage > 20) {
                        hpBar.classList.add('hp-medium');
                    } else {
                        hpBar.classList.add('hp-low');
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