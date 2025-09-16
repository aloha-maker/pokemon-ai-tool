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
    const captureButton = document.getElementById('capture-button');
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
            windowSelect.innerHTML = '<option value="">ウィンドウを選択...</option>'; // クリアしてプレースホルダーを追加
            
            data.windows.forEach(title => {
                const option = document.createElement('option');
                option.value = title;
                option.textContent = title;
                windowSelect.appendChild(option);
            });

            // 前回の選択を復元しようと試みる
            if (data.windows.includes(currentSelection)){
                windowSelect.value = currentSelection;
            }

        } catch (error) {
            console.error('ウィンドウリストの取得中にエラーが発生しました:', error);
        }
    }

    // 更新ボタンのイベントリスナー
    if (windowRefreshButton) {
        windowRefreshButton.addEventListener('click', updateWindowList);
    }

    // キャプチャボタンのイベントリスナー
    if (captureButton) {
        captureButton.addEventListener('click', async () => {
            const windowTitle = windowSelect.value;
            if (!windowTitle) {
                alert('キャプチャ対象のウィンドウを選択してください。');
                return;
            }

            const spinner = captureButton.querySelector('.spinner-border');
            spinner.classList.remove('d-none');
            captureButton.disabled = true;
            windowRefreshButton.disabled = true;

            try {
                const response = await fetch('/api/capture', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ window_title: windowTitle }),
                });

                const data = await response.json();

                if (response.ok) {
                    captureImage.src = data.file_path + '?t=' + new Date().getTime();
                } else {
                    console.error('キャプチャに失敗しました:', data.error || '不明なエラー');
                    alert(`キャプチャに失敗しました: ${data.error || '不明なエラー'}`);
                }
            } catch (error) {
                console.error('キャプチャAPIの呼び出し中にエラーが発生しました:', error);
                alert('キャプチャAPIの呼び出し中にエラーが発生しました。');
            } finally {
                spinner.classList.add('d-none');
                captureButton.disabled = false;
                windowRefreshButton.disabled = false;
            }
        });
    }

    // --- WebSocket Logic for Real-time Suggestions ---
    const socket = io();
    const suggestionOverlay = document.getElementById('suggestion-overlay');
    const suggestionAction = document.getElementById('suggestion-action');
    const suggestionValue = document.getElementById('suggestion-value');
    const suggestionReason = document.getElementById('suggestion-reason');

    socket.on('connect', () => {
        console.log('WebSocket connected!');
    });

    socket.on('suggestion_update', (data) => {
        console.log('Suggestion received:', data);
        suggestionAction.textContent = data.action;
        suggestionValue.textContent = data.value;
        suggestionReason.textContent = data.reason;
        suggestionOverlay.style.display = 'block';
        suggestionOverlay.classList.remove('fade-in');
        void suggestionOverlay.offsetWidth;
        suggestionOverlay.classList.add('fade-in');
    });

    // 初期化処理
    updateWindowList();
});