// realtimeAnalysis.js - リアルタイム解析機能

import { escapeHTML } from './utils.js';

export class RealtimeAnalysis {
    constructor() {
        this.socket = io();
        this.windowSelect = document.getElementById('window-select');
        this.windowRefreshButton = document.getElementById('window-refresh-button');
        this.toggleAnalysisButton = document.getElementById('toggle-analysis-button');
        this.captureImage = document.getElementById('capture-image');
        this.suggestionRefreshButton = document.getElementById('suggestion-refresh-button');
        this.recognizePartyBtn = document.getElementById('recognize-opponent-party-btn');
        this.logOutput = document.getElementById('realtime-log-output'); // 追加
        this.startCameraBtn = document.getElementById('start-camera-btn');
        this.startOcrBtn = document.getElementById('start-ocr-btn');
        this.startBattleBtn = document.getElementById('start-battle-btn');
        this.battleIdDisplay = document.getElementById('battle-id-display');
        this.logBuffer = [];
        this.sequence = 0;
        
        if (this.toggleAnalysisButton) {
            this.init();
        }
    }

    init() {
        this.setUIState('stopped');
        this.updateWindowList();
        this.initSocketListeners();
        
        this.windowRefreshButton?.addEventListener('click', () => this.updateWindowList());
        this.toggleAnalysisButton?.addEventListener('click', () => this.handleToggleAnalysis());
        this.suggestionRefreshButton?.addEventListener('click', () => this.socket.emit('get_suggestion', {}));
        this.recognizePartyBtn?.addEventListener('click', () => this.handleRecognizeParty());
        this.startCameraBtn?.addEventListener('click', () => this.handleStartCamera());
        this.startOcrBtn?.addEventListener('click', () => this.handleStartOcr());
        this.startBattleBtn?.addEventListener('click', () => this.handleStartBattle());

        // バトルIDの有無に応じてパーティ保存ボタンの状態を更新
        if (this.battleIdDisplay) {
            const savePartyBtn = document.getElementById('save-party-button');
            if (savePartyBtn) {
                // 初期状態を設定
                savePartyBtn.disabled = !this.battleIdDisplay.value;

                // inputイベントを監視してボタンの状態を更新
                this.battleIdDisplay.addEventListener('input', () => {
                    savePartyBtn.disabled = !this.battleIdDisplay.value;
                });
            }
        }
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
            const gameState = data.state;

            // リアルタイムログの表示
            if (this.logOutput && gameState) {
                this.appendRealtimeLog(gameState);
            }

            // AIの行動提案をリクエスト
            this.socket.emit('get_suggestion', {});
        });

        this.socket.on('suggestion_update', (data) => {
            console.log('Suggestion received:', data);
            this.displaySuggestion(data);
        });
    }

    appendRealtimeLog(state) {
        const logEntry = document.createElement('div');
        logEntry.classList.add('log-entry', 'mb-2', 'pb-1', 'border-bottom', 'border-secondary', 'border-opacity-25');

        const timestamp = new Date().toLocaleTimeString();
        let content = `<div class="text-muted small">[${timestamp}]</div>`;

        const rawResult = state.raw_ocr_result;
        let hasContent = false;

        if (rawResult && typeof rawResult === 'object' && Object.keys(rawResult).length > 0) {
            content += '<ul class="list-unstyled mb-0 small">';
            for (const [key, value] of Object.entries(rawResult)) {
                if (value && String(value).trim()) { // 値が空や空白でない場合のみ表示
                    content += `<li><span class="text-info" style="min-width: 180px; display: inline-block;">${escapeHTML(key)}:</span> <strong>${escapeHTML(value)}</strong></li>`;
                    hasContent = true;
                }
            }
            content += '</ul>';
        }
        
        // 表示すべき内容がある場合のみログに追加
        if (hasContent) {
            logEntry.innerHTML = content;
            this.logOutput.prepend(logEntry);
        }

        // ログが50件を超えたら古いものを削除
        if (this.logOutput.children.length > 50) {
            this.logOutput.removeChild(this.logOutput.lastChild);
        }

        // バッファへの保存処理
        if (hasContent) {
            for (const [key, value] of Object.entries(rawResult)) {
                if (value && String(value).trim()) {
                    this.logBuffer.push({
                        sequence: this.sequence,
                        roi_name: key,
                        ocr_text: value
                    });
                }
            }
            this.sequence++; // 内容のあるイベントのみシーケンスを進める
        }
    }

    setUIState(state) {
        this.currentState = state;
        const btn = this.toggleAnalysisButton;
        const cameraBtn = this.startCameraBtn;
        const ocrBtn = this.startOcrBtn;
        const battleBtn = this.startBattleBtn;

        // デフォルト状態
        btn.disabled = false;
        cameraBtn.disabled = false;
        ocrBtn?.disabled = true;
        battleBtn.disabled = true;
        this.windowSelect.disabled = false;
        this.windowRefreshButton.disabled = false;
        this.recognizePartyBtn.disabled = true;

        btn.dataset.state = 'stopped';
        btn.innerHTML = '<i class="bi bi-play-circle-fill"></i> 解析を開始';
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-primary');

        cameraBtn.innerHTML = '<i class="bi bi-camera-video-fill"></i> 仮想カメラ読込';
        cameraBtn.classList.remove('btn-danger');
        cameraBtn.classList.add('btn-info');

        if (state === 'stopped') {
            // デフォルトのまま
        } else if (state === 'running_window') {
            btn.dataset.state = 'running';
            btn.innerHTML = '<i class="bi bi-stop-circle-fill"></i> 停止';
            btn.classList.add('btn-danger');
            cameraBtn.disabled = true;
            this.windowSelect.disabled = true;
            this.windowRefreshButton.disabled = true;
            this.recognizePartyBtn.disabled = false;
        } else if (state === 'running_camera') {
            cameraBtn.innerHTML = '<i class="bi bi-stop-circle-fill"></i> 停止';
            cameraBtn.classList.add('btn-danger');
            btn.disabled = true;
            ocrBtn?.disabled = false;
            battleBtn.disabled = false;
            this.windowSelect.disabled = true;
            this.windowRefreshButton.disabled = true;
            this.recognizePartyBtn.disabled = false;
        } else if (state === 'running_camera_ocr') {
            cameraBtn.innerHTML = '<i class="bi bi-stop-circle-fill"></i> 停止';
            cameraBtn.classList.add('btn-danger');
            btn.disabled = true;
            ocrBtn?.disabled = true; // OCR実行中は無効
            battleBtn.disabled = true;
            this.windowSelect.disabled = true;
            this.windowRefreshButton.disabled = true;
            this.recognizePartyBtn.disabled = false;
        }
    }

    handleStartCamera() {
        const cameraIndex = document.getElementById('camera-index-input').value || 0;
        if (this.currentState === 'running_camera' || this.currentState === 'running_camera_ocr') {
            this.socket.emit('stop_analysis', {});
        } else {
            this.clearLogs();
            this.socket.emit('start_camera', { camera_index: parseInt(cameraIndex, 10) });
        }
    }

    handleStartOcr() {
        if (this.currentState === 'running_camera') {
            this.socket.emit('start_ocr', {});
        }
    }

    async handleStartBattle() {
        // OCR開始処理を呼び出す
        this.handleStartOcr();
        // 新しいバトルIDを取得・設定する
        await this.fetchAndSetNewBattleId();
    }

    async fetchAndSetNewBattleId() {
        try {
            const response = await fetch('/api/battle/new_id');
            if (!response.ok) {
                throw new Error('サーバーからバトルIDを取得できませんでした。');
            }
            const data = await response.json();
            if (data.battle_id) {
                if (this.battleIdDisplay) {
                    this.battleIdDisplay.value = data.battle_id;
                    this.battleIdDisplay.dispatchEvent(new Event('input'));
                }
                console.log(`Fetched Battle ID: ${data.battle_id}`);
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
            this.logOutput.innerHTML = ''; // 画面のログもクリア
        }
    }

    getLogBuffer() {
        return this.logBuffer;
    }

    async updateWindowList() {
        try {
            const response = await fetch('/api/windows');
            const data = await response.json();
            
            if (data.error) {
                console.error('ウィンドウリストの取得に失敗しました:', data.error);
                return;
            }
            
            const currentSelection = this.windowSelect.value;
            this.windowSelect.innerHTML = '<option value="">ウィンドウを選択...</option>';
            
            data.windows.forEach(title => {
                const option = document.createElement('option');
                option.value = title;
                option.textContent = title;
                this.windowSelect.appendChild(option);
            });

            if (data.windows.includes(currentSelection)){
                this.windowSelect.value = currentSelection;
            }

        } catch (error) {
            console.error('ウィンドウリストの取得中にエラーが発生しました:', error);
        }
    }

    handleToggleAnalysis() {
        if (this.currentState === 'running_window') {
            console.log('Requesting to stop analysis.');
            this.socket.emit('stop_analysis', {});
        } else {
            const windowTitle = this.windowSelect.value;
            if (!windowTitle) {
                alert('キャプチャ対象のウィンドウを選択してください。');
                return;
            }
            this.clearLogs();
            console.log(`Requesting to start analysis for window: ${windowTitle}`);
            this.socket.emit('start_analysis', { window_title: windowTitle });
        }
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

            // バトル中アドバイスタブをアクティブにする
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

            console.log('Received data from API:', data); // デバッグ用に追加

            if (data.success && data.party) {
                const opponentInputs = document.querySelectorAll('#opponent-party-display .pokemon-input');
                data.party.forEach((pokemonName, index) => {
                    if (opponentInputs[index]) {
                        opponentInputs[index].value = pokemonName || ''; // 認識失敗時は空にする
                    }
                });
            } else {
                alert(`パーティの認識に失敗しました: ${data.error || '不明なエラー'}`);
            }
        } catch (error) {
            console.error('パーティ認識APIの呼び出し中にエラーが発生しました:', error);
            alert('パーティの認識中にエラーが発生しました。');
        } finally {
            this.recognizePartyBtn.disabled = false;
            this.recognizePartyBtn.innerHTML = originalHtml;
        }
    }
}