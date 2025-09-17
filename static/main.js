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
    if (generatePartyButton) {
        generatePartyButton.addEventListener('click', async () => {
            const availablePokemonEl = document.getElementById('available-pokemon');
            const conceptEl = document.getElementById('tactical-concept');
            const resultArea = document.getElementById('party-generation-result-area');

            const available_pokemon = availablePokemonEl.value.split('\n').filter(p => p.trim() !== '');
            const concept = conceptEl.value;

            if (available_pokemon.length < 6) {
                alert('使用可能なポケモンを6体以上入力してください。');
                return;
            }
            if (!concept) {
                alert('戦術コンセプトを入力してください。');
                return;
            }

            const spinner = generatePartyButton.querySelector('.spinner-border');
            spinner.classList.remove('d-none');
            generatePartyButton.disabled = true;

            try {
                const response = await fetch('/generate-party', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ available_pokemon, concept }),
                });

                const data = await response.json();

                if (response.ok) {
                    displayGeneratedParty(data, resultArea);
                } else {
                    resultArea.innerHTML = `<div class="alert alert-danger">エラー: ${data.error || '不明なエラー'}</div>`;
                }
            } catch (error) {
                console.error('パーティ生成APIの呼び出し中にエラーが発生しました:', error);
                resultArea.innerHTML = `<div class="alert alert-danger">APIの呼び出しに失敗しました。</div>`;
            } finally {
                spinner.classList.add('d-none');
                generatePartyButton.disabled = false;
            }
        });
    }

    function displayGeneratedParty(data, container) {
        let partyHtml = '<h5>提案パーティ</h5><div class="row g-2 mb-3">';
        data.party.forEach(p => {
            partyHtml += `
                <div class="col-6">
                    <div class="glass-card p-2 small">
                        <div class="fw-bold">${p.name}</div>
                        <div class="text-muted">役割: ${p.role}</div>
                    </div>
                </div>
            `;
        });
        partyHtml += '</div>';

        let manualHtml = '<h5>運用ガイド</h5>';
        // 改行を<br>に変換して表示
        manualHtml += `<div class="glass-card p-3 small">${data.manual.replace(/\n/g, '<br>')}</div>`;

        container.innerHTML = partyHtml + manualHtml;
    }

    const predictButton = document.getElementById('predict-button');
    if (predictButton) {
        predictButton.addEventListener('click', async () => {
            const myPartyInputs = document.querySelectorAll('#my-party-form input');
            const opponentPartyInputs = document.querySelectorAll('#opponent-party-form input');
            const resultArea = document.getElementById('prediction-result-area');

            const my_party = Array.from(myPartyInputs).map(input => input.value).filter(p => p.trim() !== '');
            const opponent_party = Array.from(opponentPartyInputs).map(input => input.value).filter(p => p.trim() !== '');

            if (my_party.length !== 6 || opponent_party.length !== 6) {
                alert('自分と相手のパーティをそれぞれ6体ずつ入力してください。');
                return;
            }

            const spinner = predictButton.querySelector('.spinner-border');
            spinner.classList.remove('d-none');
            predictButton.disabled = true;

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ my_party, opponent_party }),
                });

                const data = await response.json();

                if (response.ok) {
                    displayPredictionResult(data, resultArea);
                } else {
                    resultArea.innerHTML = `<div class="alert alert-danger">エラー: ${data.error || '不明なエラー'}</div>`;
                }
            } catch (error) {
                console.error('選出予測APIの呼び出し中にエラーが発生しました:', error);
                resultArea.innerHTML = `<div class="alert alert-danger">APIの呼び出しに失敗しました。</div>`;
            } finally {
                spinner.classList.add('d-none');
                predictButton.disabled = false;
            }
        });
    }

    function displayPredictionResult(data, container) {
        let html = '<h5>AI推奨選出</h5>';
        html += '<div class="row g-3 text-center">';
        data.recommended_team.forEach(name => {
            html += `
                <div class="col-4">
                    <div class="glass-card p-3">
                        <div class="fw-bold fs-5">${name}</div>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        html += '<h5 class="mt-4">選出理由</h5>';
        html += `<p class="text-muted">${data.reason}</p>`;

        container.innerHTML = html;
    }

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