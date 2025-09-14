document.addEventListener('DOMContentLoaded', () => {
    const dashboardModal = document.getElementById('dashboard-modal');
    let winRateChart = null; // チャートのインスタンスを保持する変数

    // ダッシュボードモーダルが表示されたときにデータを取得
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

    function updateDashboardUI(data) {
        // 1. サマリー情報を更新
        document.getElementById('total-matches').textContent = data.stats.total_matches;
        document.getElementById('total-wins').textContent = data.stats.total_wins;
        document.getElementById('win-rate').textContent = `${data.stats.win_rate}%`;

        // 2. 対戦履歴テーブルを更新
        const tableBody = document.getElementById('history-table-body');
        tableBody.innerHTML = ''; // テーブルをクリア
        data.raw_history.forEach(match => {
            const mySelection = JSON.parse(match.my_selection).join(', ');
            const opponentParty = JSON.parse(match.opponent_party).join(', ');
            const resultClass = match.result === 'win' ? 'text-success' : 'text-danger';
            const resultText = match.result === 'win' ? '勝利' : '敗北';
            
            const row = `
                <tr>
                    <td class="small text-muted">${new Date(match.created_at).toLocaleString()}</td>
                    <td class="fw-bold ${resultClass}">${resultText}</td>
                    <td class="small">${mySelection}</td>
                    <td class="small text-muted">${opponentParty}</td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });

        // 3. 勝率グラフ（ドーナツチャート）を更新
        const ctx = document.getElementById('winRateChart').getContext('2d');
        const wins = data.stats.total_wins;
        const losses = data.stats.total_matches - wins;

        if (winRateChart) {
            winRateChart.destroy(); // 既存のチャートがあれば破棄
        }
        
        winRateChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['勝利', '敗北'],
                datasets: [{
                    data: [wins, losses],
                    backgroundColor: ['rgba(22, 160, 133, 0.7)', 'rgba(192, 57, 43, 0.7)'],
                    borderColor: ['#16A085', '#C0392B'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#ffffff'
                        }
                    },
                    title: {
                        display: true,
                        text: '勝敗割合',
                        color: '#ffffff'
                    }
                }
            }
        });
    }
});