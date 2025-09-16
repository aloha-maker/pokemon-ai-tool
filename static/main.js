document.addEventListener('DOMContentLoaded', () => {
    const dashboardModal = document.getElementById('dashboard-modal');
    let winRateChart = null; // チャートのインスタンスを保持する変数

    // ダッシュボードモーダルが表示されたときにデータを取得
    if (dashboardModal) {
        dashboardModal.addEventListener('show.bs.modal', async () => {
            try {
                const response = await fetch('/api/history');
                const data = await response.json();

                if (data.error) {
                    console.error(data.error);
                    return;
                }
                updateDashboardUI(data);
            } catch (error) {
                console.error('履歴の取得に失敗しました:', error);
            }
        });
    }

    function updateDashboardUI(data) {
        // ... (ここは変更なし、ただし簡略化のため省略) ...
    }

    const generatePartyButton = document.getElementById('generate-party-button');
    // ... (パーティ生成関連のロジックも変更なし) ...

    const predictButton = document.getElementById('predict-button');
    // ... (予測関連のロジックも変更なし) ...

    // --- Real-time Analysis Logic ---
    const windowSelect = document.getElementById('window-select');
    const windowRefreshButton = document.getElementById('window-refresh-button');
    const toggleAnalysisButton = document.getElementById('toggle-analysis-button');
    const captureImage = document.getElementById('capture-image');

    // ウィンドウリストを更新する関数
    async function updateWindowList() {
        try {
            const response = await fetch('/api/windows');
            const data = await response.json();
            if (data.error) {
                console.error('ウィンドウリストの取得に失敗しました:', data.error);
                return;
            }
            
            const currentSelection = windowSelect.value;
            windowSelect.innerHTML = '<option value="">ウィンドウを選択...</option>';
            
            data.windows.forEach(title => {
                const option = document.createElement('option');
                option.value = title;
                option.textContent = title;
                windowSelect.appendChild(option);
            });

            if (data.windows.includes(currentSelection)){
                windowSelect.value = currentSelection;
            }

        } catch (error) {
            console.error('ウィンドウリストの取得中にエラーが発生しました:', error);
        }
    }

    if (windowRefreshButton) {
        windowRefreshButton.addEventListener('click', updateWindowList);
    }

    // 解析開始・停止ボタンのロジック
    if (toggleAnalysisButton) {
        toggleAnalysisButton.addEventListener('click', () => {
            const state = toggleAnalysisButton.dataset.state;

            if (state === 'stopped') {
                const windowTitle = windowSelect.value;
                if (!windowTitle) {
                    alert('キャプチャ対象のウィンドウを選択してください。');
                    return;
                }
                console.log(`Requesting to start analysis for window: ${windowTitle}`);
                socket.emit('start_analysis', { window_title: windowTitle });

            } else if (state === 'running') {
                console.log('Requesting to stop analysis.');
                socket.emit('stop_analysis', {});
            }
        });
    }

    // --- WebSocket Logic for Real-time Suggestions ---
    const socket = io();
    const suggestionOverlay = document.getElementById('suggestion-overlay');
    const suggestionAction = document.getElementById('suggestion-action');
    const suggestionValue = document.getElementById('suggestion-value');
    const suggestionReason = document.getElementById('suggestion-reason');
    const suggestionRefreshButton = document.getElementById('suggestion-refresh-button');
    const ocrDebugCode = document.querySelector('#ocr-debug-content code');

    socket.on('connect', () => {
        console.log('WebSocket connected!');
    });

    socket.on('analysis_started', () => {
        console.log('Analysis started by server.');
        toggleAnalysisButton.dataset.state = 'running';
        toggleAnalysisButton.innerHTML = '<i class="bi bi-stop-circle-fill"></i> 解析を停止';
        toggleAnalysisButton.classList.remove('btn-primary');
        toggleAnalysisButton.classList.add('btn-danger');
        windowSelect.disabled = true;
        windowRefreshButton.disabled = true;
    });

    socket.on('analysis_stopped', (data) => {
        console.log('Analysis stopped by server.');
        if (data && data.error) {
            alert(`解析が停止しました: ${data.error}`);
        }
        toggleAnalysisButton.dataset.state = 'stopped';
        toggleAnalysisButton.innerHTML = '<i class="bi bi-play-circle-fill"></i> 解析を開始';
        toggleAnalysisButton.classList.remove('btn-danger');
        toggleAnalysisButton.classList.add('btn-primary');
        windowSelect.disabled = false;
        windowRefreshButton.disabled = false;
    });

    // バックエンドからのOCR結果を受け取る (デバッグ用)
    socket.on('ocr_update', (data) => {
        // 1. OCRデバッグ情報を更新
        if (ocrDebugCode) {
            ocrDebugCode.textContent = JSON.stringify(data.state, null, 2);
        }

        // 2. キャプチャ画像を更新
        if (data.image_url) {
            captureImage.src = data.image_url + '?t=' + new Date().getTime(); // キャッシュを無効化
        }

        // 3. AIの提案を要求
        socket.emit('get_suggestion', {});
    });

    // バックエンドからのAIの提案を受け取る
    socket.on('suggestion_update', (data) => {
        console.log('Suggestion received:', data);
        if (data && data.action) {
            suggestionAction.textContent = data.action;
            suggestionValue.textContent = data.target || ''; // targetがない場合もある
            suggestionReason.textContent = data.reason;
            
            suggestionOverlay.style.display = 'block';
            suggestionOverlay.classList.remove('fade-in');
            void suggestionOverlay.offsetWidth; // Reflow to restart animation
            suggestionOverlay.classList.add('fade-in');
        } else {
            // AIがまだ判断できない場合
            suggestionOverlay.style.display = 'none';
        }
    });

    // 更新ボタンを手動でクリックしたとき
    if (suggestionRefreshButton) {
        suggestionRefreshButton.addEventListener('click', () => {
            console.log('Manually requesting suggestion...');
            socket.emit('get_suggestion', {});
        });
    }

    // 初期化処理
    updateWindowList();
});