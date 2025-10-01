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
        this.ocrDebugCode = document.querySelector('#ocr-debug-content code');
        
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

            this.captureImage.src = "https://placehold.co/1280x720/0c0a24/e5bfff?text=Game+Capture+Preview";
        });

        this.socket.on('ocr_update', (data) => {
            if (this.ocrDebugCode) {
                this.ocrDebugCode.textContent = JSON.stringify(data.state, null, 2);
            }
            this.socket.emit('get_suggestion', {});
        });

        this.socket.on('suggestion_update', (data) => {
            console.log('Suggestion received:', data);
            this.displaySuggestion(data);
        });
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
}
