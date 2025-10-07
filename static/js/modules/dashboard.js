// static/js/modules/dashboard.js - 新しい分析ダッシュボード機能

// Chart.jsのインスタンスを保持する変数
let rankHistoryChart = null;
let mySelectionRateChart = null;

export class DashboardManager {
    constructor() {
        this.modal = document.getElementById('dashboard-modal');
        if (this.modal) {
            this.init();
        }
    }

    init() {
        this.modal.addEventListener('show.bs.modal', () => {
            this.loadDashboardData();
        });

        // イベントリスナーを一度だけ設定
        const analyzeBtn = document.getElementById('customization-analyze-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeCustomization());
        }
    }

    async loadDashboardData() {
        const loadingEl = document.getElementById('dashboard-loading');
        const contentEl = document.getElementById('dashboard-content');
        
        loadingEl.classList.remove('d-none');
        contentEl.classList.add('d-none');

        try {
            const response = await fetch('/api/dashboard');
            if (!response.ok) {
                throw new Error(`APIエラー: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();
            this.updateUI(data);

        } catch (error) {
            console.error('ダッシュボードデータの取得に失敗しました:', error);
            showAlert('dashboard-alert-container', 'ダッシュボードデータの取得に失敗しました。', 'danger');
        } finally {
            loadingEl.classList.add('d-none');
            contentEl.classList.remove('d-none');
        }
    }

    updateUI(data) {
        // 1. サマリー
        this.updateSummary(data.summary);
        this.renderRankHistoryChart(data.summary.rank_history);

        // 2. ポケモン別分析
        this.populateTable('opponent-ranking-tbody', data.opponent_ranking, ['#', 'pokemon_name', 'count']);
        this.populateTable('watch-out-pokemon-tbody', data.watch_out_pokemon, ['pokemon_name', 'win_rate', 'total_matches']);
        this.populateTable('good-at-pokemon-tbody', data.good_at_pokemon, ['pokemon_name', 'win_rate', 'total_matches']);

        // 3. 選出分析
        this.renderMySelectionRateChart(data.my_selection_rate);
        this.populateTable('selection-pattern-tbody', data.selection_pattern_win_rate, ['pattern', 'win_rate', 'total_matches']);

        // 4. 環境メタ分析
        this.setupCustomizationSelect(data.opponent_ranking);
    }

    updateSummary(summary) {
        document.getElementById('summary-win-rate').textContent = `${summary.win_rate}%`;
        document.getElementById('summary-total-matches').textContent = summary.total_matches;
        document.getElementById('summary-wins').textContent = summary.wins;
        document.getElementById('summary-losses').textContent = summary.losses;
    }

    renderRankHistoryChart(rankHistory) {
        const ctx = document.getElementById('rank-history-chart').getContext('2d');
        const labels = rankHistory.map(h => new Date(h.date).toLocaleDateString());
        const data = rankHistory.map(h => h.rank);

        if (rankHistoryChart) {
            rankHistoryChart.destroy();
        }

        rankHistoryChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'ランク',
                    data: data,
                    borderColor: '#8A2BE2',
                    backgroundColor: 'rgba(138, 43, 226, 0.1)',
                    fill: true,
                    tension: 0.3,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: false, ticks: { color: '#fff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                    x: { ticks: { color: '#fff' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    populateTable(tbodyId, data, columns) {
        const tbody = document.getElementById(tbodyId);
        tbody.innerHTML = '';
        if (!data || data.length === 0) {
            const colSpan = columns.length;
            tbody.innerHTML = `<tr><td colspan="${colSpan}" class="text-center text-muted">データがありません</td></tr>`;
            return;
        }

        data.forEach((item, index) => {
            const tr = document.createElement('tr');
            columns.forEach(column => {
                const td = document.createElement('td');
                if (column === '#') {
                    td.textContent = index + 1;
                } else if (column === 'win_rate') {
                    td.textContent = `${item[column]}%`;
                } else if (Array.isArray(item[column])) {
                    td.textContent = item[column].join(', ');
                } else {
                    td.textContent = item[column];
                }
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    renderMySelectionRateChart(selectionRateData) {
        const ctx = document.getElementById('my-selection-rate-chart').getContext('2d');
        const labels = selectionRateData.map(p => p.pokemon_name);
        const data = selectionRateData.map(p => p.selection_rate);

        if (mySelectionRateChart) {
            mySelectionRateChart.destroy();
        }

        mySelectionRateChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: ['#9B59B6', '#3498DB', '#2ECC71', '#F1C40F', '#E74C3C', '#1ABC9C'],
                    borderColor: '#2c2c2c',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#fff' } }
                }
            }
        });
    }

    setupCustomizationSelect(opponentRanking) {
        const select = document.getElementById('customization-pokemon-select');
        select.innerHTML = '<option selected value="">分析したいポケモンを選択...</option>';
        opponentRanking.forEach(p => {
            const option = document.createElement('option');
            option.value = p.pokemon_name;
            option.textContent = p.pokemon_name;
            select.appendChild(option);
        });
    }

    async analyzeCustomization() {
        const pokemonName = document.getElementById('customization-pokemon-select').value;
        if (!pokemonName) return;

        const resultsDiv = document.getElementById('customization-results');
        const analyzeBtn = document.getElementById('customization-analyze-btn');
        const originalBtnText = analyzeBtn.innerHTML;
        analyzeBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 分析中...`;
        analyzeBtn.disabled = true;

        try {
            const response = await fetch(`/api/dashboard/customization?pokemon_name=${encodeURIComponent(pokemonName)}`);
            if (!response.ok) {
                throw new Error('カスタマイズデータの取得に失敗しました。');
            }
            const data = await response.json();

            const renderList = (ulId, items, type) => {
                const ul = document.getElementById(ulId);
                ul.innerHTML = '';
                if (items && items.length > 0) {
                    items.forEach(item => {
                        let name = '';
                        if (type === 'moves') {
                            // movesはJSON文字列なのでパースする
                            try {
                                name = JSON.parse(item.moves).join(', ');
                            } catch(e) { name = item.moves; }
                        } else {
                            name = item.item || item.terastal_type;
                        }
                        ul.innerHTML += `<li>${name} <span class="text-muted">(${item.count}回)</span></li>`;
                    });
                } else {
                    ul.innerHTML = '<li class="text-muted">データなし</li>';
                }
            };

            renderList('customization-moves-ul', data.moves, 'moves');
            renderList('customization-items-ul', data.items, 'items');
            renderList('customization-teras-ul', data.terastal_types, 'teras');

            resultsDiv.classList.remove('d-none');

        } catch (error) {
            console.error('カスタマイズデータの分析中にエラーが発生しました:', error);
            showAlert('dashboard-alert-container', 'カスタマイズデータの分析に失敗しました。', 'danger');
        } finally {
            analyzeBtn.innerHTML = originalBtnText;
            analyzeBtn.disabled = false;
        }
    }
}