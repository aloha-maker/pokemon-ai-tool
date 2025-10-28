// realtimeAnalysis.js - リアルタイム解析機能

import { escapeHTML } from './utils.js';

export class RealtimeAnalysis {
    constructor() {
        this.socket = io();
        this.captureImage = document.getElementById('capture-image');
        this.suggestionRefreshButton = document.getElementById('suggestion-refresh-button');
        this.recognizePartyBtn = document.getElementById('recognize-opponent-party-btn');
        this.logOutput = document.getElementById('realtime-log-output'); // 追加
        this.startCameraBtn = document.getElementById('start-camera-btn');
        this.startBattleBtn = document.getElementById('start-battle-btn');
        this.battleIdDisplay = document.getElementById('battle-id-display');
        this.logBuffer = [];
        this.sequence = 0;
        
        this.init();
    }

    init() {
        this.setUIState('stopped');
        this.initSocketListeners();
        
        this.suggestionRefreshButton?.addEventListener('click', () => this.socket.emit('get_suggestion', {}));
        this.recognizePartyBtn?.addEventListener('click', () => this.handleRecognizeParty());
        this.startCameraBtn?.addEventListener('click', () => this.handleStartCamera());
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
        const cameraBtn = this.startCameraBtn;
        const battleBtn = this.startBattleBtn;

        // デフォルト状態
        if (cameraBtn) cameraBtn.disabled = false;
        if (battleBtn) battleBtn.disabled = true;
        if (this.recognizePartyBtn) this.recognizePartyBtn.disabled = true;

        if (cameraBtn) {
            cameraBtn.innerHTML = '<i class="bi bi-camera-video-fill"></i> 仮想カメラ読込';
            cameraBtn.classList.remove('btn-danger');
            cameraBtn.classList.add('btn-info');
        }

        if (state === 'stopped') {
            // デフォルトのまま
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
        console.log("handleStartCamera called!"); // デバッグログ
        const cameraIndex = document.getElementById('camera-index-input').value || 0;
        if (this.currentState === 'running_camera' || this.currentState === 'running_camera_ocr') {
            this.socket.emit('stop_analysis', {});
        } else {
            this.clearLogs();
            console.log(`Attempting to emit start_camera with index: ${cameraIndex}`); // デバッグログ
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

            if (data.status === 'success' && data.data.party) {
                const opponentInputs = document.querySelectorAll('#opponent-party-display .pokemon-input');
                data.data.party.forEach((pokemonName, index) => {
                    if (opponentInputs[index]) {
                        opponentInputs[index].value = pokemonName || ''; // 認識失敗時は空にする
                        // ポケモンアイコンと種族値の更新をトリガーするために、手動でchangeイベントを発火させます。
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
}