import { showAlert } from './utils.js';

// Chart.jsのインスタンスを保持する変数
let rankHistoryChart = null;
let mySelectionRateChart = null;

/**
 * APIからダッシュボード全体のデータを取得する
 * @returns {Promise<object|null>}
 */
async function fetchDashboardData() {
    try {
        const response = await fetch('/api/dashboard');
        const jsonResponse = await response.json();

        if (!response.ok || jsonResponse.status !== 'success') {
            const errorInfo = (jsonResponse.data && jsonResponse.data.error) || jsonResponse.message || `APIエラー: ${response.status}`;
            throw new Error(errorInfo);
        }

        return jsonResponse.data;
    } catch (error) {
        console.error('ダッシュボードデータの取得に失敗しました:', error);
        showAlert(`ダッシュボードデータの取得に失敗しました: ${error.message}`, 'danger', 'dashboard-alert-container');
        return null;
    }
}

/**
 * サマリーカードを更新する
 * @param {object} summary
 */
function updateSummary(summary) {
    document.getElementById('summary-win-rate').textContent = `${summary.win_rate}%`;
    document.getElementById('summary-total-matches').textContent = summary.total_matches;
    document.getElementById('summary-wins').textContent = summary.wins;
    document.getElementById('summary-losses').textContent = summary.losses;
}

/**
 * ランク推移チャートを描画または更新する
 * @param {Array<object>} rankHistory
 */
function renderRankHistoryChart(rankHistory) {
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
                y: {
                    beginAtZero: false,
                    ticks: {
                        color: '#fff'
                    },
                     grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: {
                        color: '#fff'
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

/**
 * テーブルのボディをデータで埋める汎用関数
 * @param {string} tbodyId - テーブルボディのID
 * @param {Array<object>} data - 表示するデータの配列
 * @param {Array<string>} columns - 表示するカラムのキーの配列
 */
function populateTable(tbodyId, data, columns) {
    const tbody = document.getElementById(tbodyId);
    tbody.innerHTML = ''; // 既存の内容をクリア
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
            } else if (column.includes('.')) {
                // ネストされたプロパティに対応 (例: 'pokemon.name')
                td.textContent = column.split('.').reduce((o, i) => o[i], item);
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

/**
 * 自分の選出率チャートを描画または更新する
 * @param {Array<object>} selectionRateData
 */
function renderMySelectionRateChart(selectionRateData) {
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
                backgroundColor: [
                    '#9B59B6', '#3498DB', '#2ECC71', '#F1C40F', '#E74C3C', '#1ABC9C'
                ],
                borderColor: '#2c2c2c',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#fff'
                    }
                }
            }
        }
    });
}

/**
 * 環境メタ分析のポケモン選択プルダウンをセットアップする
 * @param {Array<object>} opponentRanking
 */
function setupCustomizationSelect(opponentRanking) {
    const select = document.getElementById('customization-pokemon-select');
    select.innerHTML = '<option selected>分析したいポケモンを選択...</option>';
    opponentRanking.forEach(p => {
        const option = document.createElement('option');
        option.value = p.pokemon_name;
        option.textContent = p.pokemon_name;
        select.appendChild(option);
    });
}

/**
 * 特定のポケモンのカスタマイズデータを取得して表示する
 */
async function analyzeCustomization() {
    const pokemonName = document.getElementById('customization-pokemon-select').value;
    if (!pokemonName) return;

    const resultsDiv = document.getElementById('customization-results');
    resultsDiv.classList.add('d-none');

    try {
        const response = await fetch(`/api/dashboard/customization?pokemon_name=${pokemonName}`);
        const jsonResponse = await response.json();

        if (!response.ok || jsonResponse.status !== 'success') {
            const errorInfo = (jsonResponse.data && jsonResponse.data.error) || jsonResponse.message || 'カスタマイズデータの取得に失敗しました。';
            throw new Error(errorInfo);
        }
        
        const data = jsonResponse.data;

        const renderList = (ulId, items) => {
            const ul = document.getElementById(ulId);
            ul.innerHTML = '';
            if (items.length > 0) {
                items.forEach(item => {
                    const key = Object.keys(item)[0];
                    ul.innerHTML += `<li>${item[key]} <span class="text-muted">(${item.count}回)</span></li>`;
                });
            } else {
                ul.innerHTML = '<li class="text-muted">データなし</li>';
            }
        };

        renderList('customization-moves-ul', data.moves);
        renderList('customization-items-ul', data.items);
        renderList('customization-teras-ul', data.terastal_types);

        resultsDiv.classList.remove('d-none');

    } catch (error) {
        console.error('カスタマイズデータの分析中にエラーが発生しました:', error);
        showAlert(`カスタマイズデータの分析に失敗しました: ${error.message}`, 'danger', 'dashboard-alert-container');
    }
}

/**
 * ダッシュボードを初期化し、すべてのデータをロードして表示する
 */
export async function initDashboard() {
    const loadingEl = document.getElementById('dashboard-loading');
    const contentEl = document.getElementById('dashboard-content');
    
    loadingEl.classList.remove('d-none');
    contentEl.classList.add('d-none');

    const data = await fetchDashboardData();

    if (data) {
        // 1. サマリー
        updateSummary(data.summary);
        renderRankHistoryChart(data.summary.rank_history);

        // 2. ポケモン別分析
        populateTable('opponent-ranking-tbody', data.opponent_ranking, ['#', 'pokemon_name', 'count']);
        populateTable('watch-out-pokemon-tbody', data.watch_out_pokemon, ['pokemon_name', 'win_rate', 'total_matches']);
        populateTable('good-at-pokemon-tbody', data.good_at_pokemon, ['pokemon_name', 'win_rate', 'total_matches']);

        // 3. 選出分析
        renderMySelectionRateChart(data.my_selection_rate);
        populateTable('selection-pattern-tbody', data.selection_pattern_win_rate, ['pattern', 'win_rate', 'total_matches']);

        // 4. 環境メタ分析
        setupCustomizationSelect(data.opponent_ranking);
        document.getElementById('customization-analyze-btn').addEventListener('click', analyzeCustomization);
        
        loadingEl.classList.add('d-none');
        contentEl.classList.remove('d-none');
    }
}
