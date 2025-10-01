// videoAnalysis.js - 動画解析機能

import { escapeHTML, showAlert } from './utils.js';

export class VideoAnalysis {
    constructor() {
        this.modal = document.getElementById('video-manager-modal');
        this.videoFileInput = document.getElementById('video-file-input');
        this.videoUploadButton = document.getElementById('video-upload-button');
        this.videoUploadProgress = document.getElementById('video-upload-progress');
        this.videoTasksTbody = document.getElementById('video-tasks-tbody');
        this.pollingIntervals = {};
        
        if (this.videoUploadButton) {
            this.init();
        }
    }

    init() {
        this.videoUploadButton.addEventListener('click', () => {
            const file = this.videoFileInput.files[0];
            if (!file) {
                showAlert('video-upload-alert', 'ファイルが選択されていません。', 'danger');
                return;
            }
            this.uploadVideo(file);
        });
    }

    uploadVideo(file) {
        const formData = new FormData();
        formData.append('video', file);
        const xhr = new XMLHttpRequest();

        xhr.open('POST', '/api/videos/upload', true);

        const spinner = this.videoUploadButton.querySelector('.spinner-border');
        spinner.classList.remove('d-none');
        this.videoUploadButton.disabled = true;
        this.videoUploadProgress.parentElement.style.display = 'block';
        this.videoUploadProgress.style.width = '0%';
        document.getElementById('video-upload-alert').style.display = 'none';

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                this.videoUploadProgress.style.width = percentComplete + '%';
            }
        };

        xhr.onload = () => {
            spinner.classList.add('d-none');
            this.videoUploadButton.disabled = false;
            this.videoUploadProgress.parentElement.style.display = 'none';

            if (xhr.status === 202) {
                const response = JSON.parse(xhr.responseText);
                showAlert('video-upload-alert', 
                    `アップロード成功!解析を開始しました。(Task ID: ${response.task_id})`, 'success');
                this.addTaskToList(response.task_id, file.name);
                this.startPolling(response.task_id);
            } else {
                const errorMsg = JSON.parse(xhr.responseText).error || '不明なエラーが発生しました。';
                showAlert('video-upload-alert', `アップロード失敗: ${errorMsg}`, 'danger');
            }
        };

        xhr.onerror = () => {
            spinner.classList.add('d-none');
            this.videoUploadButton.disabled = false;
            this.videoUploadProgress.parentElement.style.display = 'none';
            showAlert('video-upload-alert', 'アップロード中にネットワークエラーが発生しました。', 'danger');
        };

        xhr.send(formData);
    }

    addTaskToList(taskId, fileName) {
        const placeholder = this.videoTasksTbody.querySelector('.text-center');
        if (placeholder) placeholder.remove();

        const newRow = document.createElement('tr');
        newRow.id = `task-${taskId}`;
        newRow.innerHTML = `
            <td>${escapeHTML(fileName)}</td>
            <td><small>${taskId}</small></td>
            <td><span class="badge bg-secondary">PENDING</span></td>
            <td><button class="btn btn-sm btn-outline-light" disabled>結果表示</button></td>
        `;
        this.videoTasksTbody.prepend(newRow);
    }

    startPolling(taskId) {
        if (this.pollingIntervals[taskId]) {
            clearInterval(this.pollingIntervals[taskId]);
        }

        this.pollingIntervals[taskId] = setInterval(async () => {
            try {
                const response = await fetch(`/api/videos/status/${taskId}`);
                if (!response.ok) throw new Error(`Server responded with ${response.status}`);
                
                const data = await response.json();
                this.updateTaskStatus(taskId, data);

                if (data.status === 'DONE' || data.status === 'ERROR') {
                    clearInterval(this.pollingIntervals[taskId]);
                    delete this.pollingIntervals[taskId];
                }
            } catch (error) {
                console.error(`[Task ${taskId}] Polling error:`, error);
                clearInterval(this.pollingIntervals[taskId]);
                delete this.pollingIntervals[taskId];
                this.updateTaskStatus(taskId, { status: 'ERROR', result: { error: 'Polling failed' } });
            }
        }, 3000);
    }

    updateTaskStatus(taskId, data) {
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
                actionButton.onclick = () => this.showResult(data.result.log_id);
            } else {
                actionButton.textContent = 'IDなし';
                actionButton.disabled = true;
            }
        } else if (data.status === 'ERROR') {
            actionButton.disabled = true;
            actionButton.textContent = '失敗';
        }
    }

    async showResult(logId) {
        const resultBody = document.getElementById('video-result-body');
        const resultModal = new bootstrap.Modal(document.getElementById('video-result-modal'));
        
        resultBody.innerHTML = '<div class="text-center p-5"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        resultModal.show();

        try {
            const response = await fetch(`/api/videos/result/${logId}`);
            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Failed to fetch result');

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
}
