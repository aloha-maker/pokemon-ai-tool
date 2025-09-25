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
    let lastGeneratedParty = null; // 生成されたパーティ情報を保持する

    if (generatePartyButton) {
        generatePartyButton.addEventListener('click', async () => {
            const availablePokemonEl = document.getElementById('available-pokemon');
            const conceptEl = document.getElementById('tactical-concept');
            const resultArea = document.getElementById('party-generation-result-area');
            const registerArea = document.getElementById('register-party-area');
            const registerAlert = document.getElementById('register-party-alert');

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
            registerArea.classList.add('d-none'); // 登録エリアを隠す
            registerAlert.style.display = 'none';

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
                    lastGeneratedParty = data.party; // 結果を保存
                    displayGeneratedParty(data, resultArea);
                    registerArea.classList.remove('d-none'); // 登録エリアを表示
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
            const movesHtml = p.moves.map(m => `<li>${escapeHTML(m.name)}</li>`).join('');
            partyHtml += `
                <div class="col-6">
                    <div class="glass-card p-2 small">
                        <div class="fw-bold">${escapeHTML(p.name)}</div>
                        <div class="text-muted">役割: ${escapeHTML(p.role)}</div>
                        <div><strong>持ち物:</strong> ${escapeHTML(p.item_name)}</div>
                        <div><strong>特性:</strong> ${escapeHTML(p.ability_name)}</div>
                        <div><strong>性格:</strong> ${escapeHTML(p.nature_name)}</div>
                        <div><strong>テラス:</strong> ${escapeHTML(p.tera_type_name)}</div>
                        <ul class="list-unstyled small mt-1 mb-0"><strong>技:</strong>${movesHtml}</ul>
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

    const registerGeneratedPartyBtn = document.getElementById('register-generated-party-btn');
    if (registerGeneratedPartyBtn) {
        registerGeneratedPartyBtn.addEventListener('click', async () => {
            if (!lastGeneratedParty) {
                alert('登録するパーティデータがありません。先にパーティを生成してください。');
                return;
            }

            const partyName = prompt('登録するパーティ名を入力してください:', 'AI生成パーティ');
            if (!partyName || partyName.trim() === '') {
                return; // ユーザーがキャンセルまたは空の名前を入力
            }

            const registerAlert = document.getElementById('register-party-alert');
            const spinner = registerGeneratedPartyBtn.querySelector('.spinner-border'); // Assuming button has a spinner
            
            registerGeneratedPartyBtn.disabled = true;
            if(spinner) spinner.classList.remove('d-none');

            try {
                const response = await fetch('/api/register-generated-party', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ party: lastGeneratedParty, party_name: partyName })
                });

                const result = await response.json();
                
                if (response.ok) {
                    showAlert('register-party-alert', result.message, 'success');
                } else {
                    showAlert('register-party-alert', `エラー: ${result.error}`, 'danger');
                }

            } catch (error) {
                showAlert('register-party-alert', '登録中に不明なエラーが発生しました。', 'danger');
            } finally {
                registerGeneratedPartyBtn.disabled = false;
                if(spinner) spinner.classList.add('d-none');
            }
        });
    }

    // ポケモンIDに基づいて特性の選択肢を更新する関数
    async function updateAbilitiesForPokemon(pokemonId) {
        const abilitySelect = document.getElementById('ability-id');
        if (pokemonId) {
            try {
                const response = await fetch(`/api/pokemon/${pokemonId}/abilities`);
                if (!response.ok) throw new Error('Failed to fetch abilities');
                const abilities = await response.json();
                populateSelect('ability-id', abilities, '特性を選択');
            } catch (error) {
                console.error('Error fetching abilities:', error);
                populateSelect('ability-id', [], '特性の取得に失敗');
            }
        } else {
            populateSelect('ability-id', [], '先にポケモンを選択');
        }
    }

    // --- 選出予測パーティ読み込み ---
    const myPartySelect = document.getElementById('my-party-select');
    const loadMyPartyBtn = document.getElementById('load-my-party-btn');

    async function initMyPartySelector() {
        if (!myPartySelect) return;
        try {
            const response = await fetch('/api/parties');
            if (!response.ok) throw new Error('パーティ一覧の取得に失敗しました。');
            const parties = await response.json();
            
            myPartySelect.innerHTML = '<option selected value="">登録済みパーティから選ぶ...</option>'; // クリア
            parties.forEach(party => {
                const option = document.createElement('option');
                option.value = party.id;
                option.textContent = party.name;
                myPartySelect.appendChild(option);
            });
        } catch (error) {
            console.error(error);
        }
    }

    async function loadPartyToForm() {
        const partyId = myPartySelect.value;
        if (!partyId) {
            alert('パーティを選択してください。');
            return;
        }

        try {
            const response = await fetch(`/api/parties/${partyId}`);
            if (!response.ok) throw new Error('パーティ情報の取得に失敗しました。');
            const party = await response.json();
            
            const myPartyInputs = document.querySelectorAll('#my-party-form input');
            
            // フォームをクリア
            myPartyInputs.forEach(input => input.value = '');

            // 取得したメンバーをフォームに設定
            party.members.forEach((member, index) => {
                if (index < myPartyInputs.length) {
                    myPartyInputs[index].value = member.pokemon_name;
                }
            });

        } catch (error) {
            console.error(error);
            alert(error.message);
        }
    }

    if (loadMyPartyBtn) {
        loadMyPartyBtn.addEventListener('click', loadPartyToForm);
    }
    // --- ここまで追加 ---

    const predictButton = document.getElementById('predict-button');
    if (predictButton) {
        predictButton.addEventListener('click', async () => {
            const opponentPartyInputs = document.querySelectorAll('#opponent-party-form input');
            const resultArea = document.getElementById('prediction-result-area');

            const opponent_party = Array.from(opponentPartyInputs).map(input => input.value).filter(p => p.trim() !== '');

            let requestBody = { opponent_party };

            const selectedPartyId = myPartySelect.value;

            if (selectedPartyId) {
                requestBody.my_party_id = selectedPartyId;
            } else {
                const myPartyInputs = document.querySelectorAll('#my-party-form input');
                const my_party = Array.from(myPartyInputs).map(input => input.value).filter(p => p.trim() !== '');
                if (my_party.length !== 6) {
                    alert('自分のパーティを6体入力するか、登録済みパーティを読み込んでください。');
                    return;
                }
                requestBody.my_party = my_party;
            }

            if (opponent_party.length !== 6) {
                alert('相手のパーティをそれぞれ6体ずつ入力してください。');
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
                    body: JSON.stringify(requestBody),
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

    socket.on('analysis_started', (data) => {
        console.log('Analysis started by server.');
        toggleAnalysisButton.dataset.state = 'running';
        toggleAnalysisButton.innerHTML = '<i class="bi bi-stop-circle-fill"></i> 解析を停止';
        toggleAnalysisButton.classList.remove('btn-primary');
        toggleAnalysisButton.classList.add('btn-danger');
        windowSelect.disabled = true;
        windowRefreshButton.disabled = true;

        // 映像ストリームをプレビューに設定
        if (data.video_feed_url) {
            captureImage.src = data.video_feed_url;
        }
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

        // プレビューをプレースホルダーに戻す
        captureImage.src = "https://placehold.co/1280x720/0c0a24/e5bfff?text=Game+Capture+Preview";
    });

    // バックエンドからのOCR結果を受け取る (デバッグ用)
    socket.on('ocr_update', (data) => {
        // 1. OCRデバッグ情報を更新
        if (ocrDebugCode) {
            ocrDebugCode.textContent = JSON.stringify(data.state, null, 2);
        }

        // 2. AIの提案を要求
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

    // --- Video Analysis Logic ---
    const videoManagerModal = document.getElementById('video-manager-modal');
    const videoFileInput = document.getElementById('video-file-input');
    const videoUploadButton = document.getElementById('video-upload-button');
    const videoUploadProgress = document.getElementById('video-upload-progress');
    const videoUploadAlert = document.getElementById('video-upload-alert');
    const videoTasksTbody = document.getElementById('video-tasks-tbody');

    const pollingIntervals = {}; // task_id: intervalId

    // アップロードボタンのクリックイベント
    if (videoUploadButton) {
        videoUploadButton.addEventListener('click', () => {
            const file = videoFileInput.files[0];
            if (!file) {
                showAlert('video-upload-alert', 'ファイルが選択されていません。', 'danger');
                return;
            }
            uploadVideo(file);
        });
    }

    function uploadVideo(file) {
        const formData = new FormData();
        formData.append('video', file);

        const xhr = new XMLHttpRequest();

        xhr.open('POST', '/api/videos/upload', true);

        // UIをアップロード中状態に更新
        const spinner = videoUploadButton.querySelector('.spinner-border');
        spinner.classList.remove('d-none');
        videoUploadButton.disabled = true;
        videoUploadProgress.parentElement.style.display = 'block';
        videoUploadProgress.style.width = '0%';
        videoUploadAlert.style.display = 'none';

        // 進捗イベント
        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                videoUploadProgress.style.width = percentComplete + '%';
            }
        };

        // 完了イベント
        xhr.onload = () => {
            spinner.classList.add('d-none');
            videoUploadButton.disabled = false;
            videoUploadProgress.parentElement.style.display = 'none';

            if (xhr.status === 202) {
                const response = JSON.parse(xhr.responseText);
                showAlert('video-upload-alert', `アップロード成功！解析を開始しました。(Task ID: ${response.task_id})`, 'success');
                addTaskToList(response.task_id, file.name);
                startPolling(response.task_id);
            } else {
                const errorMsg = JSON.parse(xhr.responseText).error || '不明なエラーが発生しました。';
                showAlert('video-upload-alert', `アップロード失敗: ${errorMsg}`, 'danger');
            }
        };

        // エラーイベント
        xhr.onerror = () => {
            spinner.classList.add('d-none');
            videoUploadButton.disabled = false;
            videoUploadProgress.parentElement.style.display = 'none';
            showAlert('video-upload-alert', 'アップロード中にネットワークエラーが発生しました。', 'danger');
        };

        xhr.send(formData);
    }
    
    function addTaskToList(taskId, fileName) {
        const placeholder = videoTasksTbody.querySelector('.text-center');
        if (placeholder) {
            placeholder.remove();
        }

        const newRow = document.createElement('tr');
        newRow.id = `task-${taskId}`;
        newRow.innerHTML = `
            <td>${escapeHTML(fileName)}</td>
            <td><small>${taskId}</small></td>
            <td><span class="badge bg-secondary">PENDING</span></td>
            <td><button class="btn btn-sm btn-outline-light" disabled>結果表示</button></td>
        `;
        videoTasksTbody.prepend(newRow);
    }

    function startPolling(taskId) {
        if (pollingIntervals[taskId]) {
            clearInterval(pollingIntervals[taskId]);
        }

        pollingIntervals[taskId] = setInterval(async () => {
            try {
                const response = await fetch(`/api/videos/status/${taskId}`);
                if (!response.ok) {
                    throw new Error(`Server responded with ${response.status}`);
                }
                const data = await response.json();
                updateTaskStatus(taskId, data);

                if (data.status === 'DONE' || data.status === 'ERROR') {
                    clearInterval(pollingIntervals[taskId]);
                    delete pollingIntervals[taskId];
                }
            } catch (error) {
                console.error(`[Task ${taskId}] Polling error:`, error);
                clearInterval(pollingIntervals[taskId]);
                delete pollingIntervals[taskId];
                updateTaskStatus(taskId, { status: 'ERROR', result: { error: 'Polling failed' } });
            }
        }, 3000);
    }

    function updateTaskStatus(taskId, data) {
        const taskRow = document.getElementById(`task-${taskId}`);
        if (!taskRow) return;

        const statusBadge = taskRow.querySelector('.badge');
        const actionButton = taskRow.querySelector('button');

        let badgeClass = 'bg-secondary';
        switch (data.status) {
            case 'PENDING':    badgeClass = 'bg-secondary'; break;
            case 'PROCESSING': badgeClass = 'bg-primary'; break;
            case 'DONE':       badgeClass = 'bg-success'; break;
            case 'ERROR':      badgeClass = 'bg-danger'; break;
        }
        statusBadge.className = `badge ${badgeClass}`;
        statusBadge.textContent = data.status;

        if (data.status === 'DONE') {
            actionButton.disabled = false;
            if (data.result && data.result.log_id) {
                actionButton.dataset.logId = data.result.log_id;
                actionButton.onclick = () => showResult(data.result.log_id);
            } else {
                actionButton.textContent = 'IDなし';
                actionButton.disabled = true;
            }
        } else if (data.status === 'ERROR') {
            actionButton.disabled = true;
            actionButton.textContent = '失敗';
        }
    }

    async function showResult(logId) {
        const resultBody = document.getElementById('video-result-body');
        const resultModal = new bootstrap.Modal(document.getElementById('video-result-modal'));
        
        resultBody.innerHTML = '<div class="text-center p-5"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        resultModal.show();

        try {
            const response = await fetch(`/api/videos/result/${logId}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch result');
            }

            let html = '';
            if (data.battle_data && data.battle_data.turns && data.battle_data.turns.length > 0) {
                html += '<h4 class="neon-text-purple mb-3">ターン詳細</h4>';
                html += '<div class="accordion" id="turns-accordion">';
                data.battle_data.turns.forEach((turn, index) => {
                    const myPokemon = turn.my_pokemon || '不明';
                    const opponentPokemon = turn.opponent_pokemon || '不明';

                    html += `
                    <div class="accordion-item glass-card-inside mb-2">
                        <h2 class="accordion-header" id="turn-heading-${index}">
                            <button class="accordion-button collapsed bg-transparent neon-text-blue" type="button" data-bs-toggle="collapse" data-bs-target="#turn-collapse-${index}">
                                Turn ${turn.turn}: ${myPokemon} vs ${opponentPokemon}
                            </button>
                        </h2>
                        <div id="turn-collapse-${index}" class="accordion-collapse collapse" data-bs-parent="#turns-accordion">
                            <div class="accordion-body">
                                <pre class="bg-dark text-light p-2 rounded small"><code>${escapeHTML(JSON.stringify(turn, null, 2))}</code></pre>
                            </div>
                        </div>
                    </div>
                    `;
                });
                html += '</div>';
            } else {
                html = '<p class="text-muted text-center">詳細なターンデータは見つかりませんでした。</p>';
            }
            resultBody.innerHTML = html;

        } catch (error) {
            resultBody.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
        }
    }

    function showAlert(alertId, message, type = 'info') {
        const alertEl = document.getElementById(alertId);
        alertEl.className = `alert alert-${type}`;
        alertEl.textContent = message;
        alertEl.style.display = 'block';
    }
    
    function escapeHTML(str) {
        if (typeof str !== 'string') {
            str = String(str);
        }
        return str.replace(/[&<"'\/]/g, function(match) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;',
                '/': '&#x2F;'
            }[match];
        });
    }

    // --- ROI Editor Logic ---
    const roiCanvas = document.getElementById('roi-canvas');
    const roiCtx = roiCanvas.getContext('2d');
    const roiSelector = document.getElementById('roi-selector');
    const saveRoiBtn = document.getElementById('save-roi-btn');
    const roiCoordsEl = document.getElementById('roi-coords');

    const roiImageUpload = document.getElementById('roi-image-upload');

    let roiConfig = {};
    let roiImage = new Image();
    let isDrawing = false;
    let startX, startY;

    async function initRoiEditor() {
        try {
            const [imgPathResponse, configResponse] = await Promise.all([
                fetch('/api/roi/image_path'),
                fetch('/api/roi/config')
            ]);
            const imgPathData = await imgPathResponse.json();
            roiConfig = await configResponse.json();

            roiImage.onload = () => {
                // Set canvas dimensions to a fixed 1920x1080
                roiCanvas.width = 1920;
                roiCanvas.height = 1080;
                drawRoiRects();
                updateCoordsDisplay();
            };
            // Use the captureImage src if available, otherwise use the one from the API
            const currentSrc = document.getElementById('capture-image').src;
            if (currentSrc && !currentSrc.includes('placehold.co')) {
                 roiImage.src = currentSrc;
            } else {
                 roiImage.src = imgPathData.image_path + '?t=' + new Date().getTime();
            }

        } catch (error) {
            console.error("Error initializing ROI editor:", error);
        }
    }

    function drawRoiRects() {
        roiCtx.clearRect(0, 0, roiCanvas.width, roiCanvas.height);
        // Scale the image to fit the 1920x1080 canvas
        roiCtx.drawImage(roiImage, 0, 0, roiCanvas.width, roiCanvas.height);
        roiCtx.lineWidth = 2;
        for (const key in roiConfig) {
            if (key === 'reference_resolution') continue;
            const [x, y, w, h] = roiConfig[key];
            if (key === roiSelector.value) {
                roiCtx.strokeStyle = '#00ff00'; // Green
            } else {
                roiCtx.strokeStyle = '#ff0000'; // Red
            }
            roiCtx.strokeRect(x, y, w, h);
        }
    }

    function startDrawing(e) {
        isDrawing = true;
        const rect = roiCanvas.getBoundingClientRect();
        startX = (e.clientX - rect.left) * (roiCanvas.width / rect.width);
        startY = (e.clientY - rect.top) * (roiCanvas.height / rect.height);
    }

    function draw(e) {
        if (!isDrawing) return;
        const rect = roiCanvas.getBoundingClientRect();
        const currentX = (e.clientX - rect.left) * (roiCanvas.width / rect.width);
        const currentY = (e.clientY - rect.top) * (roiCanvas.height / rect.height);
        drawRoiRects();
        roiCtx.strokeStyle = '#00ff00';
        roiCtx.strokeRect(startX, startY, currentX - startX, currentY - startY);
    }

    function stopDrawing(e) {
        if (!isDrawing) return;
        isDrawing = false;
        const selectedRoi = roiSelector.value;
        const rect = roiCanvas.getBoundingClientRect();
        const endX = (e.clientX - rect.left) * (roiCanvas.width / rect.width);
        const endY = (e.clientY - rect.top) * (roiCanvas.height / rect.height);
        const x = Math.min(startX, endX);
        const y = Math.min(startY, endY);
        const w = Math.abs(startX - endX);
        const h = Math.abs(startY - endY);
        if (w > 0 && h > 0) {
            roiConfig[selectedRoi] = [Math.round(x), Math.round(y), Math.round(w), Math.round(h)];
        }
        drawRoiRects();
        updateCoordsDisplay();
    }

    function updateCoordsDisplay() {
        const selectedRoi = roiSelector.value;
        if (roiConfig[selectedRoi]) {
            const [x, y, w, h] = roiConfig[selectedRoi];
            roiCoordsEl.textContent = `[${x}, ${y}, ${w}, ${h}]`;
        }
    }

    async function saveRoiConfig() {
        // Always set the reference resolution to 1920x1080
        roiConfig.reference_resolution = {
            width: 1920,
            height: 1080
        };
        try {
            const response = await fetch('/api/roi/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(roiConfig)
            });
            const data = await response.json();
            if (response.ok) {
                alert('ROI設定を保存しました。');
            } else {
                alert(`保存に失敗しました: ${data.error}`);
            }
        } catch (error) {
            console.error("Error saving ROI config:", error);
            alert('保存中にエラーが発生しました。');
        }
    }
    
    // Initialize ROI Editor
    const captureImageEl = document.getElementById('capture-image');
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'src') {
                // Add a small delay to ensure the image is rendered
                setTimeout(initRoiEditor, 300);
            }
        });
    });
    observer.observe(captureImageEl, { attributes: true });

    roiCanvas.addEventListener('mousedown', startDrawing);
    roiCanvas.addEventListener('mousemove', draw);
    roiCanvas.addEventListener('mouseup', stopDrawing);
    roiCanvas.addEventListener('mouseleave', stopDrawing);
            roiSelector.addEventListener('change', updateCoordsDisplay);
            saveRoiBtn.addEventListener('click', saveRoiConfig);
    
            roiImageUpload.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    roiImage.src = URL.createObjectURL(file);
                }
            });
    initRoiEditor();

    // --- F-05: Trained Pokémon Management Logic ---
    const trainedPokemonModal = document.getElementById('trained-pokemon-modal');
    const pokemonFormModal = new bootstrap.Modal(document.getElementById('pokemon-form-modal'));
    const showAddPokemonBtn = document.getElementById('show-add-pokemon-modal');
    const trainedPokemonTbody = document.getElementById('trained-pokemon-list-tbody');
    const pokemonForm = document.getElementById('pokemon-form');
    const evTotalEl = document.getElementById('ev-total');

    // 育成済みポケモンの一覧をロードしてテーブルに描画する関数
    async function loadTrainedPokemons() {
        try {
            const response = await fetch('/api/trained-pokemons');
            if (!response.ok) throw new Error('Failed to fetch trained pokemons');
            const pokemons = await response.json();

            trainedPokemonTbody.innerHTML = ''; // テーブルをクリア
            if (pokemons.length === 0) {
                trainedPokemonTbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">登録されているポケモンはいません。</td></tr>';
                return;
            }

            pokemons.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${p.id}</td>
                    <td>${escapeHTML(p.pokemon_name) || 'N/A'}</td>
                    <td>${escapeHTML(p.nickname) || ''}</td>
                    <td>${p.level}</td>
                    <td>${escapeHTML(p.tera_type_name) || 'N/A'}</td>
                    <td>${escapeHTML(p.item_name) || 'N/A'}</td>
                    <td>${escapeHTML(p.ability_name) || 'N/A'}</td>
                    <td>${escapeHTML(p.nature_name) || 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-light edit-btn" data-id="${p.id}"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${p.id}"><i class="bi bi-trash"></i></button>
                    </td>
                `;
                trainedPokemonTbody.appendChild(tr);
            });

            // イベントリスナーをボタンに設定
            attachActionListeners();

        } catch (error) {
            console.error('Error loading trained pokemons:', error);
            trainedPokemonTbody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">データの読み込みに失敗しました。</td></tr>';
        }
    }

    // 編集・削除ボタンにイベントリスナーを設定する関数
    function attachActionListeners() {
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', handleEditClick);
        });
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', handleDeleteClick);
        });
    }

    // 編集ボタンがクリックされたときの処理
    async function handleEditClick(event) {
        const id = event.currentTarget.dataset.id;
        try {
            const response = await fetch(`/api/trained-pokemons/${id}`);
            if (!response.ok) throw new Error('Failed to fetch pokemon details');
            const pokemon = await response.json();
            await showPokemonForm(pokemon);
        } catch (error) {
            console.error(`Error fetching pokemon ${id}:`, error);
            alert('ポケモンの情報の取得に失敗しました。');
        }
    }

    // 削除ボタンがクリックされたときの処理
    async function handleDeleteClick(event) {
        const id = event.currentTarget.dataset.id;
        if (confirm(`ID: ${id} のポケモンを本当に削除しますか？`)) {
            try {
                const response = await fetch(`/api/trained-pokemons/${id}`, { method: 'DELETE' });
                if (!response.ok) throw new Error('Failed to delete pokemon');
                showAlert('trained-pokemon-alert', 'ポケモンを削除しました。', 'success'); // 仮のアラート
                loadTrainedPokemons(); // 一覧を再読み込み
            } catch (error) {
                console.error(`Error deleting pokemon ${id}:`, error);
                alert('削除に失敗しました。');
            }
        }
    }

    // ポケモン登録・編集フォームを表示する関数
    async function showPokemonForm(pokemon = null) {
        pokemonForm.reset();
        document.getElementById('pokemon-id').value = '';

        // フォームの全フィールドを一旦リセット
        const fields = ['pokemon-master-id', 'nickname', 'level', 'tera-type-id', 'held-item-id', 'ability-id', 'nature-id', 'move1-id', 'move2-id', 'move3-id', 'move4-id', 'ev-hp', 'ev-atk', 'ev-def', 'ev-spa', 'ev-spd', 'ev-spe'];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });

        if (pokemon) {
            // 編集の場合、フォームにデータを設定
            document.getElementById('pokemon-id').value = pokemon.id || '';
            document.getElementById('pokemon-master-id').value = pokemon.pokemon_id || '';
            document.getElementById('nickname').value = pokemon.nickname || '';
            document.getElementById('level').value = pokemon.level || 50;
            document.getElementById('tera-type-id').value = pokemon.tera_type_id || '';
            document.getElementById('held-item-id').value = pokemon.held_item_id || '';
            
            // ★★★ 修正箇所 ★★★
            // 先に特性リストを読み込んでから、値を設定する
            await updateAbilitiesForPokemon(pokemon.pokemon_id);
            document.getElementById('ability-id').value = pokemon.ability_id || '';
            // ★★★ ここまで ★★★

            document.getElementById('nature-id').value = pokemon.nature_id || '';
            
            document.getElementById('ev-hp').value = pokemon.ev_hp || 0;
            document.getElementById('ev-atk').value = pokemon.ev_atk || 0;
            document.getElementById('ev-def').value = pokemon.ev_def || 0;
            document.getElementById('ev-spa').value = pokemon.ev_spa || 0;
            document.getElementById('ev-spd').value = pokemon.ev_spd || 0;
            document.getElementById('ev-spe').value = pokemon.ev_spe || 0;

            // 技情報を設定
            for (let i = 1; i <= 4; i++) {
                document.getElementById(`move${i}-id`).value = pokemon[`move${i}_id`] || '';
            }
        } else {
            // 新規登録の場合は、特性プルダウンを初期状態にする
            await updateAbilitiesForPokemon(null);
        }
        updateEvTotal();
        pokemonFormModal.show();
    }

    // フォームが送信されたときの処理
    async function handleFormSubmit(event) {
        event.preventDefault();
        const id = document.getElementById('pokemon-id').value;
        const formData = {
            pokemon_id: document.getElementById('pokemon-master-id').value,
            nickname: document.getElementById('nickname').value,
            level: document.getElementById('level').value,
            tera_type_id: document.getElementById('tera-type-id').value,
            held_item_id: document.getElementById('held-item-id').value,
            ability_id: document.getElementById('ability-id').value,
            nature_id: document.getElementById('nature-id').value,
            move1_id: document.getElementById('move1-id').value,
            move2_id: document.getElementById('move2-id').value,
            move3_id: document.getElementById('move3-id').value,
            move4_id: document.getElementById('move4-id').value,
            ev_hp: document.getElementById('ev-hp').value,
            ev_atk: document.getElementById('ev-atk').value,
            ev_def: document.getElementById('ev-def').value,
            ev_spa: document.getElementById('ev-spa').value,
            ev_spd: document.getElementById('ev-spd').value,
            ev_spe: document.getElementById('ev-spe').value,
        };

        const url = id ? `/api/trained-pokemons/${id}` : '/api/trained-pokemons';
        const method = id ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            if (!response.ok) throw new Error('Failed to save pokemon');
            pokemonFormModal.hide();
            loadTrainedPokemons();
        } catch (error) {
            console.error('Error saving pokemon:', error);
            alert('保存に失敗しました。');
        }
    }

    // 努力値の合計を計算して表示
    function updateEvTotal() {
        let total = 0;
        document.querySelectorAll('.ev-input').forEach(input => {
            total += Number(input.value) || 0;
        });
        evTotalEl.textContent = total;
        if (total > 510) {
            evTotalEl.classList.add('text-danger');
        } else {
            evTotalEl.classList.remove('text-danger');
        }
    }

    // --- イベントリスナーの設定 ---
    if (trainedPokemonModal) {
        trainedPokemonModal.addEventListener('show.bs.modal', loadTrainedPokemons);
    }
    if (showAddPokemonBtn) {
        showAddPokemonBtn.addEventListener('click', () => showPokemonForm());
    }
    if (pokemonForm) {
        pokemonForm.addEventListener('submit', handleFormSubmit);
    }
    document.querySelectorAll('.ev-input').forEach(input => {
        input.addEventListener('change', updateEvTotal);
    });

    // ポケモン、技、特性などのマスターデータを取得し、セレクトボックスを初期化する
    async function initFormSelects() {
        const resources = {
            'pokemon-master-id': 'pokemons',
            'tera-type-id': 'types',
            'held-item-id': 'items',
            // 'ability-id': 'abilities', // 動的に読み込むため削除
            'nature-id': 'natures'
        };
        const moveSelects = document.querySelectorAll('.move-select');

        try {
            const requests = Object.values(resources).map(res => fetch(`/api/master/${res}`))
            const moveRequest = fetch('/api/master/moves');
            const responses = await Promise.all([...requests, moveRequest]);

            for(const res of responses) {
                if (!res.ok) throw new Error(`Failed to fetch master data: ${res.statusText}`);
            }

            const dataPromises = responses.map(res => res.json());
            const [pokemons, types, items, natures, moves] = await Promise.all(dataPromises);

            // オートコンプリート用のdatalistを生成
            if (document.getElementById('pokemon-datalist') === null) {
                const pokemonDatalist = document.createElement('datalist');
                pokemonDatalist.id = 'pokemon-datalist';
                const pokemonNames = new Set();
                pokemons.forEach(pokemon => {
                    const name = pokemon.name_ja || pokemon.name;
                    if (name) {
                        pokemonNames.add(name);
                    }
                });

                pokemonNames.forEach(name => {
                    const option = document.createElement('option');
                    option.value = name;
                    pokemonDatalist.appendChild(option);
                });
                document.body.appendChild(pokemonDatalist);
            }

            populateSelect('pokemon-master-id', pokemons, 'ポケモンを選択');
            populateSelect('tera-type-id', types, 'テラスタイプを選択');
            populateSelect('held-item-id', items, '持ち物を選択');
            // populateSelect('ability-id', abilities, '特性を選択'); // 動的に読み込むため削除
            populateSelect('nature-id', natures, '性格を選択');

            moveSelects.forEach(select => {
                populateSelect(select.id, moves, '技を選択');
            });

            // ポケモン選択時に特性を動的に読み込むイベントリスナー
            const pokemonMasterSelect = document.getElementById('pokemon-master-id');
            if (pokemonMasterSelect) {
                pokemonMasterSelect.addEventListener('change', (event) => {
                    updateAbilitiesForPokemon(event.target.value);
                });
            }

            console.log("フォームの選択肢を初期化しました。");

        } catch (error) {
            console.error("マスターデータの初期化に失敗しました:", error);
            alert("フォームの初期化に失敗しました。ページをリロードしてみてください。");
        }
    }

    function populateSelect(elementId, data, defaultOptionText) {
        const select = document.getElementById(elementId);
        if (!select) return;

        select.innerHTML = ''; // クリア
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = defaultOptionText;
        select.appendChild(defaultOption);

        data.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = item.name_ja || item.name; // 日本語名がなければ英語名
            select.appendChild(option);
        });
    }

    initFormSelects();

    // --- F-06: Party Management Logic (Modal) ---
    const partyManagementModal = document.getElementById('party-management-modal');
    if (partyManagementModal) {
        const partyForm = document.getElementById('party-form');
        const partyList = document.getElementById('party-list');
        const partyIdField = document.getElementById('party-id');
        const partyNameField = document.getElementById('party-name');
        const partyDescriptionField = document.getElementById('party-description');
        const memberSelects = partyManagementModal.querySelectorAll('.member-select');
        const formTitle = document.getElementById('party-form-title');
        const submitButton = partyForm.querySelector('button[type="submit"]');
        const cancelEditBtn = document.getElementById('cancel-edit-btn');

        let allTrainedPokemons = []; // 育成済みポケモン一覧をキャッシュ
        let isDataLoaded = false; // APIデータのロード状態を管理

        // モーダルが表示されるたびにUIを更新
        partyManagementModal.addEventListener('show.bs.modal', async () => {
            // APIデータが未取得の場合のみロード
            if (!isDataLoaded) {
                await loadAndPopulateTrainedPokemons();
                isDataLoaded = true;
            } else {
                // データが既にあれば、ドロップダウンの選択肢のみ再設定
                populateMemberSelects();
            }
            // パーティ一覧は毎回最新のものを取得
            await loadAndDisplayParties();
        });

        // 初期化処理（イベントリスナーの設定）
        function initPartyManagement() {
            partyForm.addEventListener('submit', handlePartyFormSubmit);
            cancelEditBtn.addEventListener('click', resetPartyForm);
        }

        // 育成済みポケモンをAPIからロードする
        async function loadAndPopulateTrainedPokemons() {
            try {
                const response = await fetch('/api/trained-pokemons');
                if (!response.ok) throw new Error('Failed to fetch trained pokemons');
                allTrainedPokemons = await response.json();
                populateMemberSelects(); // ドロップダウンを埋める
            } catch (error) {
                console.error('Error loading trained pokemons:', error);
                partyList.innerHTML = '<div class="alert alert-danger">育成済みポケモンの読み込みに失敗しました。</div>';
            }
        }

        // キャッシュされたデータでドロップダウンを埋める
        function populateMemberSelects() {
            memberSelects.forEach(select => {
                const currentValue = select.value;
                select.innerHTML = '<option value="">メンバーを選択...</option>'; // クリア
                allTrainedPokemons.forEach(p => {
                    const option = document.createElement('option');
                    option.value = p.id;
                    option.textContent = `${p.nickname || p.pokemon_name} (ID: ${p.id})`;
                    select.appendChild(option);
                });
                select.value = currentValue; // 元の選択値を維持しようと試みる
            });
        }

        // パーティ一覧をロードして表示
        async function loadAndDisplayParties() {
            try {
                const response = await fetch('/api/parties');
                if (!response.ok) throw new Error('Failed to fetch parties');
                const parties = await response.json();

                partyList.innerHTML = '';
                if (parties.length === 0) {
                    partyList.innerHTML = '<p class="text-muted text-center">登録されているパーティはありません。</p>';
                    return;
                }

                parties.forEach(party => {
                    const partyCard = document.createElement('div');
                    partyCard.className = 'col-lg-6 mb-3';
                    let membersHtml = '<ul class="list-group list-group-flush small">';
                    party.members.forEach(member => {
                        membersHtml += `<li class="list-group-item bg-transparent">${escapeHTML(member.nickname || member.pokemon_name)}</li>`;
                    });
                     if (party.members.length < 6) {
                        for(let i = party.members.length; i < 6; i++) {
                             membersHtml += `<li class="list-group-item bg-transparent text-muted">-</li>`;
                        }
                    }
                    membersHtml += '</ul>';

                    partyCard.innerHTML = `
                        <div class="card h-100 glass-card-inside">
                            <div class="card-body p-2">
                                <h6 class="card-title">${escapeHTML(party.name)}</h6>
                                <p class="card-text text-muted small mb-1">${escapeHTML(party.description || '')}</p>
                                ${membersHtml}
                            </div>
                            <div class="card-footer bg-transparent border-top-0 text-end p-2">
                                <button class="btn btn-sm btn-outline-light edit-party-btn" data-id="${party.id}"><i class="bi bi-pencil"></i></button>
                                <button class="btn btn-sm btn-outline-danger delete-party-btn" data-id="${party.id}"><i class="bi bi-trash"></i></button>
                            </div>
                        </div>
                    `;
                    partyList.appendChild(partyCard);
                });

                // イベントリスナーを再設定
                partyList.querySelectorAll('.edit-party-btn').forEach(btn => {
                    btn.addEventListener('click', handlePartyEditClick);
                });
                partyList.querySelectorAll('.delete-party-btn').forEach(btn => {
                    btn.addEventListener('click', handlePartyDeleteClick);
                });

            } catch (error) {
                console.error('Error loading parties:', error);
                partyList.innerHTML = '<div class="alert alert-danger">パーティ一覧の読み込みに失敗しました。</div>';
            }
        }

        // フォーム送信処理
        async function handlePartyFormSubmit(event) {
            event.preventDefault();
            const partyId = partyIdField.value;
            const members = Array.from(memberSelects).reduce((acc, s) => {
                if (s.value) {
                    acc.push(parseInt(s.value, 10));
                }
                return acc;
            }, []);

            // 重複チェック
            const uniqueMembers = new Set(members);
            if (uniqueMembers.size < members.length) {
                alert('パーティに同じポケモンを複数選択することはできません。');
                return;
            }

            const partyData = {
                name: partyNameField.value,
                description: partyDescriptionField.value,
                members: members
            };

            const url = partyId ? `/api/parties/${partyId}` : '/api/parties';
            const method = partyId ? 'PUT' : 'POST';

            try {
                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(partyData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Save failed');
                }

                await response.json();
                resetPartyForm();
                await loadAndDisplayParties();

            } catch (error) {
                console.error('Error saving party:', error);
                alert(`保存に失敗しました: ${error.message}`);
            }
        }

        // 編集ボタンクリック処理
        async function handlePartyEditClick(event) {
            const partyId = event.currentTarget.dataset.id;
            try {
                const response = await fetch(`/api/parties/${partyId}`);
                if (!response.ok) throw new Error('Failed to fetch party details');
                const party = await response.json();

                partyIdField.value = party.id;
                partyNameField.value = party.name;
                partyDescriptionField.value = party.description;
                
                memberSelects.forEach((select, index) => {
                    const member = party.members.find(m => m.member_index === index);
                    select.value = member ? member.trained_pokemon_id : '';
                });

                formTitle.textContent = 'パーティ編集';
                submitButton.textContent = '更新';
                cancelEditBtn.style.display = 'inline-block';

            } catch (error) {
                console.error(`Error fetching party ${partyId} for edit:`, error);
                alert('パーティ情報の読み込みに失敗しました。');
            }
        }

        // 削除ボタンクリック処理
        async function handlePartyDeleteClick(event) {
            const partyId = event.currentTarget.dataset.id;
            if (confirm(`ID: ${partyId} のパーティを本当に削除しますか？`)) {
                try {
                    const response = await fetch(`/api/parties/${partyId}`, { method: 'DELETE' });
                    if (!response.ok) throw new Error('Failed to delete party');
                    
                    await loadAndDisplayParties();

                } catch (error) {
                    console.error(`Error deleting party ${partyId}:`, error);
                    alert('削除に失敗しました。');
                }
            }
        }

        // フォームをリセットする
        function resetPartyForm() {
            partyForm.reset();
            partyIdField.value = '';
            formTitle.textContent = '新規パーティ登録';
            submitButton.textContent = '保存';
            cancelEditBtn.style.display = 'none';
        }

        // イベントリスナーを初期設定
        initPartyManagement();
    }

    // --- F-07: Calculator Logic (Modal) ---
    const calculatorModal = document.getElementById('calculator-modal');
    if (calculatorModal) {
        let isCalcInitialized = false;
        const statusCalcForm = document.getElementById('status-calc-form');
        const pokemonSelect = document.getElementById('calc-pokemon-id');
        const natureSelect = document.getElementById('calc-nature-id');
        const levelInput = document.getElementById('calc-level');
        const evInputs = statusCalcForm.querySelectorAll('.ev-calc-input');
        const evTotalEl = document.getElementById('ev-calc-total');
        const resultEl = document.getElementById('status-calc-result');

        // モーダル表示時に初期化
        calculatorModal.addEventListener('show.bs.modal', () => {
            if (!isCalcInitialized) {
                initCalculator();
                isCalcInitialized = true;
            }
        });

        // 初期化処理
        async function initCalculator() {
            // セレクトボックスのプレースホルダーを設定
            await Promise.all([
                populateSelect(pokemonSelect.id, [], 'ポケモンを選択...'),
                populateSelect(natureSelect.id, [], '性格を選択...'),
                populateSelect('attacker-move-id', [], '技を選択...'),
                populateSelect('attacker-pokemon-id', [], 'ポケモンを選択...'),
                populateSelect('defender-pokemon-id', [], 'ポケモンを選択...'),
                populateSelect('attacker-nature-id', [], '性格を選択...'),
                populateSelect('defender-nature-id', [], '性格を選択...'),
            ]);
            
            try {
                const [pokemonsRes, naturesRes, movesRes] = await Promise.all([
                    fetch('/api/master/pokemons'),
                    fetch('/api/master/natures'),
                    fetch('/api/master/moves')
                ]);
                const pokemons = await pokemonsRes.json();
                const natures = await naturesRes.json();
                const moves = await movesRes.json();

                // ステータス計算タブのセレクタ
                populateSelect(pokemonSelect.id, pokemons, 'ポケモンを選択...');
                populateSelect(natureSelect.id, natures, '性格を選択...');

                // ダメージ計算タブのセレクタ
                document.querySelectorAll('.calc-pokemon-selector').forEach(sel => populateSelect(sel.id, pokemons, 'ポケモンを選択...'));
                document.querySelectorAll('.calc-nature-selector').forEach(sel => populateSelect(sel.id, natures, '性格を選択...'));
                document.querySelectorAll('.calc-move-selector').forEach(sel => populateSelect(sel.id, moves, '技を選択...'));

            } catch (error) {
                console.error('Calculator initialization failed:', error);
                resultEl.innerHTML = '<p class="text-danger">初期化に失敗しました。</p>';
            }

            // イベントリスナーを設定
            statusCalcForm.addEventListener('change', debounce(calculateStatus, 200));
            statusCalcForm.addEventListener('input', debounce(calculateStatus, 200));
            evInputs.forEach(input => input.addEventListener('input', updateEvCalcTotal));

            const damageCalcForm = document.getElementById('damage-calc-form');
            damageCalcForm.addEventListener('change', debounce(calculateDamage, 200));
            damageCalcForm.addEventListener('input', debounce(calculateDamage, 200));
        }

        // ダメージ計算を実行して表示
        async function calculateDamage() {
            const damageResultEl = document.getElementById('damage-calc-result');
            const data = {
                attacker_level: parseInt(document.getElementById('attacker-level').value, 10) || 50,
                attack_stat: parseInt(document.getElementById('attacker-stat').value, 10) || 0,
                defender_hp: parseInt(document.getElementById('defender-hp').value, 10) || 0,
                defense_stat: parseInt(document.getElementById('defender-stat').value, 10) || 0,
                move_id: parseInt(document.getElementById('attacker-move-id').value, 10) || null,
                defender_id: parseInt(document.getElementById('defender-pokemon-id').value, 10) || null,
            };

            if (!data.attack_stat || !data.defender_hp || !data.defense_stat || !data.move_id || !data.defender_id) {
                damageResultEl.innerHTML = '<p class="text-muted">必須項目をすべて入力してください。</p>';
                return;
            }

            try {
                const response = await fetch('/api/calculate/damage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'Calculation failed');
                }

                const result = await response.json();
                displayDamageResults(result);

            } catch (error) {
                console.error('Damage calculation error:', error);
                damageResultEl.innerHTML = `<p class="text-danger">計算エラー: ${error.message}</p>`;
            }
        }

        // ダメージ計算結果を表示
        function displayDamageResults(result) {
            const damageResultEl = document.getElementById('damage-calc-result');
            const hitsToKO = result.min_hits_to_ko === result.max_hits_to_ko ?
                (result.min_hits_to_ko === Infinity ? '∞' : `確定 ${result.min_hits_to_ko}発`):
                `乱数 ${result.min_hits_to_ko}発 〜 確定 ${result.max_hits_to_ko}発`;

            damageResultEl.innerHTML = `
                <div class="row">
                    <div class="col-6">
                        <p class="mb-1">ダメージ: <strong>${result.min_damage} 〜 ${result.max_damage}</strong></p>
                        <p class="mb-0">割合: <strong>${result.min_damage_percent}% 〜 ${result.max_damage_percent}%</strong></p>
                    </div>
                    <div class="col-6">
                        <p class="mb-1">確定数: <strong>${hitsToKO}</strong></p>
                    </div>
                </div>
            `;
        }

        // ステータス計算を実行して表示
        async function calculateStatus() {
            const pokemonId = pokemonSelect.value;
            const natureId = natureSelect.value;

            if (!pokemonId || !natureId) {
                resultEl.innerHTML = '<p class="text-muted">ポケモンと性格を選択してください。</p>';
                return;
            }

            const evs = {};
            const statsOrder = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
            evInputs.forEach((input, index) => {
                const statKey = statsOrder[index];
                // バックエンドのキー名に合わせる
                const backendStatKey = statKey.replace('atk', 'attack').replace('def', 'defense').replace('spa', 'sp_attack').replace('spd', 'sp_defense').replace('spe', 'speed');
                evs[backendStatKey] = parseInt(input.value, 10) || 0;
            });

            const data = {
                pokemon_id: parseInt(pokemonId, 10),
                level: parseInt(levelInput.value, 10),
                nature_id: parseInt(natureId, 10),
                evs: evs
            };

            try {
                const response = await fetch('/api/calculate/status', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'Calculation failed');
                }

                const stats = await response.json();
                displayStatusResults(stats);

            } catch (error) {
                console.error('Status calculation error:', error);
                resultEl.innerHTML = `<p class="text-danger">計算エラー: ${error.message}</p>`;
            }
        }

        // 計算結果を表示
        function displayStatusResults(stats) {
            resultEl.innerHTML = `
                <table class="table table-sm table-borderless">
                    <tbody>
                        <tr><th>HP</th><td>${stats.hp}</td></tr>
                        <tr><th>こうげき</th><td>${stats.attack}</td></tr>
                        <tr><th>ぼうぎょ</th><td>${stats.defense}</td></tr>
                        <tr><th>とくこう</th><td>${stats.sp_attack}</td></tr>
                        <tr><th>とくぼう</th><td>${stats.sp_defense}</td></tr>
                        <tr><th>すばやさ</th><td>${stats.speed}</td></tr>
                    </tbody>
                </table>
            `;
        }

        // 努力値の合計を更新
        function updateEvCalcTotal() {
            let total = 0;
            evInputs.forEach(input => {
                total += parseInt(input.value, 10) || 0;
            });
            evTotalEl.textContent = total;
            evTotalEl.classList.toggle('text-danger', total > 510);
        }

        // debounce関数（入力イベントの発火を間引く）
        function debounce(func, delay) {
            let timeout;
            return function(...args) {
                const context = this;
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(context, args), delay);
            };
        }
    }

    // --- F-08: Simulator Logic (Step-by-step) ---
    const simulatorModal = document.getElementById('simulator-modal');
    if (simulatorModal) {
        // --- DOM Elements ---
        const setupScreen = document.getElementById('simulation-setup-screen');
        const selectionScreen = document.getElementById('simulation-selection-screen');
        const battleScreen = document.getElementById('simulation-battle-screen');
        
        const party1Select = document.getElementById('sim-party1-id');
        const party2Select = document.getElementById('sim-party2-id');
        const startBtn = document.getElementById('start-simulation-btn');
        
        const party1NameEl = document.getElementById('party1-name-display');
        const party2NameEl = document.getElementById('party2-name-display');
        const party1ListEl = document.getElementById('party1-selection-list');
        const party2ListEl = document.getElementById('party2-selection-list');
        const confirmSelectionBtn = document.getElementById('confirm-selection-btn');

        const nextTurnBtn = document.getElementById('next-turn-btn');
        const logArea = document.getElementById('simulation-log-area');

        // --- State ---
        let simulationId = null;

        // --- Functions ---

        // パーティ選択プルダウンを初期化
        async function initPartySelectors() {
            try {
                const response = await fetch('/api/parties');
                if (!response.ok) throw new Error('パーティ一覧の取得に失敗しました。');
                const parties = await response.json();
                const options = parties.map(p => ({ id: p.id, name_ja: p.name }));
                populateSelect(party1Select.id, options, 'パーティを選択...');
                populateSelect(party2Select.id, options, 'パーティを選択...');
            } catch (error) {
                console.error(error);
                logArea.innerHTML = `<p class="text-danger">${error.message}</p>`;
            }
        }

        // 対戦準備ボタンの処理
        async function handleStartSimulation() {
            const party1Id = party1Select.value;
            const party2Id = party2Select.value;

            if (!party1Id || !party2Id) {
                alert('2つのパーティを選択してください。');
                return;
            }

            setButtonLoading(startBtn, true);

            try {
                const response = await fetch('/api/simulations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ party1_id: party1Id, party2_id: party2Id })
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'シミュレーションの作成に失敗しました。');
                }

                const data = await response.json();
                simulationId = data.simulation_id;
                updateUI(data.state);

            } catch (error) {
                console.error(error);
                logArea.innerHTML = `<p class="text-danger">${error.message}</p>`;
            } finally {
                setButtonLoading(startBtn, false);
            }
        }

        // 選出完了ボタンの処理
        async function handleConfirmSelection() {
            const selection1 = Array.from(party1ListEl.querySelectorAll('input:checked')).map(cb => cb.value);
            const selection2 = Array.from(party2ListEl.querySelectorAll('input:checked')).map(cb => cb.value);

            if (selection1.length !== 3 || selection2.length !== 3) {
                alert('各パーティから3体のポケモンを選出してください。');
                return;
            }

            setButtonLoading(confirmSelectionBtn, true);

            try {
                const response = await fetch(`/api/simulations/${simulationId}/select`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ selection1, selection2 })
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || '選出の確定に失敗しました。');
                }

                const state = await response.json();
                updateUI(state);

            } catch (error) {
                console.error(error);
                logArea.innerHTML = `<p class="text-danger">${error.message}</p>`;
            } finally {
                setButtonLoading(confirmSelectionBtn, false);
            }
        }

        // ターン進行ボタンの処理
        async function handleNextTurn() {
            setButtonLoading(nextTurnBtn, true);
            try {
                const response = await fetch(`/api/simulations/${simulationId}/next_turn`, {
                    method: 'POST'
                });
                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'ターン進行に失敗しました。');
                }
                const state = await response.json();
                updateUI(state);
            } catch (error) {
                console.error(error);
                logArea.innerHTML = `<p class="text-danger">${error.message}</p>`;
            } finally {
                setButtonLoading(nextTurnBtn, false);
            }
        }

        // UIを最新の状態に更新
        function updateUI(state) {
            // ログエリアを更新
            logArea.innerHTML = state.log.join('\n');
            logArea.scrollTop = logArea.scrollHeight;

            // 画面表示を切り替え
            setupScreen.classList.toggle('d-none', state.state !== 'INITIALIZED');
            selectionScreen.classList.toggle('d-none', state.state !== 'SELECTING');
            battleScreen.classList.toggle('d-none', state.state !== 'READY_FOR_TURN' && state.state !== 'BATTLE_OVER');

            if (state.state === 'SELECTING') {
                // 選出画面の描画
                party1NameEl.textContent = `パーティ1 (ID: ${state.party1.id})`;
                party2NameEl.textContent = `パーティ2 (ID: ${state.party2.id})`;
                party1ListEl.innerHTML = renderSelectionList(state.party1.pokemons, 'party1');
                party2ListEl.innerHTML = renderSelectionList(state.party2.pokemons, 'party2');
            } else if (state.state === 'READY_FOR_TURN' || state.state === 'BATTLE_OVER') {
                // 対戦画面の描画
                updateBattleField(state);
            }
            
            // バトル終了時の処理
            if (state.state === 'BATTLE_OVER') {
                nextTurnBtn.disabled = true;
                nextTurnBtn.textContent = `対戦終了 - 勝者: ${state.winner}`;
            }
        }
        
        // 選出リストのHTMLを生成
        function renderSelectionList(pokemons, partyName) {
            return pokemons.map((p, index) => `
                <label class="list-group-item">
                    <input class="form-check-input me-1" type="checkbox" value="${index}" name="${partyName}-selection">
                    ${escapeHTML(p.nickname || p.pokemon_name)}
                </label>
            `).join('');
        }

        // 対戦フィールドを更新
        function updateBattleField(state) {
            const p1 = state.party1.pokemons[state.party1.active_pokemon_index];
            const p2 = state.party2.pokemons[state.party2.active_pokemon_index];

            updatePokemonInfo('player', p1);
            updatePokemonInfo('opponent', p2);
        }

        // 個別のポケモン情報を更新
        function updatePokemonInfo(playerType, pokemon) {
            const nameEl = document.getElementById(`${playerType}-pokemon-name`);
            const hpBarEl = document.getElementById(`${playerType}-pokemon-hp-bar`);
            const hpTextEl = document.getElementById(`${playerType}-pokemon-hp-text`);

            nameEl.textContent = pokemon.nickname || pokemon.pokemon_name;
            const hpPercent = (pokemon.current_hp / pokemon.max_hp) * 100;
            hpBarEl.style.width = `${hpPercent}%`;
            hpTextEl.textContent = `${pokemon.current_hp} / ${pokemon.max_hp}`;

            // HPに応じてバーの色を変更
            hpBarEl.classList.remove('bg-success', 'bg-warning', 'bg-danger');
            if (hpPercent > 50) {
                hpBarEl.classList.add('bg-success');
            } else if (hpPercent > 20) {
                hpBarEl.classList.add('bg-warning');
            } else {
                hpBarEl.classList.add('bg-danger');
            }
        }

        // ボタンのローディング状態を制御
        function setButtonLoading(button, isLoading) {
            const spinner = button.querySelector('.spinner-border');
            button.disabled = isLoading;
            if (spinner) {
                spinner.classList.toggle('d-none', !isLoading);
            }
        }
        
        // モーダル表示時に初期化
        simulatorModal.addEventListener('show.bs.modal', () => {
            // 状態をリセット
            simulationId = null;
            updateUI({ state: 'INITIALIZED', log: ['対戦準備ボタンを押して開始してください。'] });
            nextTurnBtn.disabled = false;
            nextTurnBtn.innerHTML = '<span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span> ターンを進める';
            initPartySelectors();
        });

        // --- Event Listeners ---
        startBtn.addEventListener('click', handleStartSimulation);
        confirmSelectionBtn.addEventListener('click', handleConfirmSelection);
        nextTurnBtn.addEventListener('click', handleNextTurn);
    }

    // 初期化処理
    initMyPartySelector();
});
