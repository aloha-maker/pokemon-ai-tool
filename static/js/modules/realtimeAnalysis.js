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
        this.logBuffer = [];
        this.sequence = 0;
        
        if (this.toggleAnalysisButton) {
            this.init();
        }
    }

    init() {
        this.updateWindowList();
        this.initSocketListeners();
        
        if (this.windowRefreshButton) {
            this.windowRefreshButton.addEventListener('click', () => this.updateWindowList());
        }
        
        if (this.toggleAnalysisButton) {
            this.toggleAnalysisButton.addEventListener('click', () => this.handleToggleAnalysis());
        }
        
        if (this.suggestionRefreshButton) {
            this.suggestionRefreshButton.addEventListener('click', () => {
                console.log('Manually requesting suggestion...');
                this.socket.emit('get_suggestion', {});
            });
        }

        if (this.recognizePartyBtn) {
            this.recognizePartyBtn.addEventListener('click', () => this.handleRecognizeParty());
        }
    }

    initSocketListeners() {
        this.socket.on('connect', () => {
            console.log('WebSocket connected!');
        });

        this.socket.on('analysis_started', (data) => {
            console.log('Analysis started by server.');
            this.toggleAnalysisButton.dataset.state = 'running';
            this.toggleAnalysisButton.innerHTML = '<i class="bi bi-stop-circle-fill"></i> 解析を停止';
            this.toggleAnalysisButton.classList.remove('btn-primary');
            this.toggleAnalysisButton.classList.add('btn-danger');
            this.windowSelect.disabled = true;
            this.windowRefreshButton.disabled = true;
            if (this.recognizePartyBtn) this.recognizePartyBtn.disabled = false;

            if (data.video_feed_url) {
                this.captureImage.src = data.video_feed_url;
            }
        });

        this.socket.on('analysis_stopped', (data) => {
            console.log('Analysis stopped by server.');
            if (data && data.error) {
                alert(`解析が停止しました: ${data.error}`);
            }
            this.toggleAnalysisButton.dataset.state = 'stopped';
            this.toggleAnalysisButton.innerHTML = '<i class="bi bi-play-circle-fill"></i> 解析を開始';
            this.toggleAnalysisButton.classList.remove('btn-danger');
            this.toggleAnalysisButton.classList.add('btn-primary');
            this.windowSelect.disabled = false;
            this.windowRefreshButton.disabled = false;
            if (this.recognizePartyBtn) this.recognizePartyBtn.disabled = true;

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
        const state = this.toggleAnalysisButton.dataset.state;

        if (state === 'stopped') {
            const windowTitle = this.windowSelect.value;
            if (!windowTitle) {
                alert('キャプチャ対象のウィンドウを選択してください。');
                return;
            }
            // 解析開始時にバッファとシーケンスをリセット
            this.logBuffer = [];
            this.sequence = 0;
            if (this.logOutput) {
                this.logOutput.innerHTML = ''; // 画面のログもクリア
            }
            console.log(`Requesting to start analysis for window: ${windowTitle}`);
            this.socket.emit('start_analysis', { window_title: windowTitle });
        } else if (state === 'running') {
            console.log('Requesting to stop analysis.');
            this.socket.emit('stop_analysis', {});
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