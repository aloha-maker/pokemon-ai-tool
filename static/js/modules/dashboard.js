// dashboard.js - ダッシュボード機能

export class DashboardManager {
    constructor() {
        this.modal = document.getElementById('dashboard-modal');
        this.winRateChart = null;
        
        if (this.modal) {
            this.init();
        }
    }

    init() {
        this.modal.addEventListener('show.bs.modal', async () => {
            try {
                const response = await fetch('/api/history');
                const data = await response.json();

                if (data.error) {
                    console.error(data.error);
                    return;
                }
                this.updateDashboardUI(data);
            } catch (error) {
                console.error('履歴の取得に失敗しました:', error);
            }
        });
    }

    updateDashboardUI(data) {
        // ダッシュボードUIの更新ロジック
        // 元のコードにあったupdateDashboardUI関数の内容をここに実装
        console.log('Dashboard data:', data);
    }
}
