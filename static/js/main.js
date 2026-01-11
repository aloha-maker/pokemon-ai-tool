// main.js - アプリケーションのエントリーポイント
import { DashboardManager } from './modules/dashboard.js';
import { PartyGenerator } from './modules/partyGenerator.js';
import { PredictionManager } from './modules/prediction.js';
import { RealtimeAnalysis } from './modules/realtimeAnalysis.js';
import { VideoAnalysis } from './modules/videoAnalysis.js';
import { ROIEditor } from './modules/roiEditor.js';
import { TrainedPokemonManager } from './modules/trainedPokemon.js';
import { PartyManagement } from './modules/partyManagement.js';
import { Calculator } from './modules/calculator.js';
import { Simulator } from './modules/simulator.js';
import { PokemonDetailEditor } from './modules/pokemonDetailEditor.js';
import { PartySaver } from './modules/partySaver.js';
import { initFormSelects } from './modules/formHelpers.js';
import { MastarData } from './collectors/mastarData.js';
import { BattleStateManager } from './collectors/battleStateManager.js';
import { Test } from './test.js';

document.addEventListener('DOMContentLoaded', async() => {
    try {
        // インスタンスを保持
        const mastarData = await MastarData.createAndLoad();
        const instances = {
            mastarData: mastarData,
            dashboardManager: new DashboardManager(),
            partyGenerator: new PartyGenerator(),
            videoAnalysis: new VideoAnalysis(),
            roiEditor: new ROIEditor(),
            trainedPokemonManager: new TrainedPokemonManager(),
            partyManagement: new PartyManagement(),
            calculator: new Calculator(),
            simulator: new Simulator(),
            predictionManager: new PredictionManager()
        };

        // Test関数をグローバルスコープに公開
        window.Test = Test;
        
        // 依存関係のある初期化
        instances.battleStateManager = new BattleStateManager(
            instances.mastarData
        );
        instances.pokemonDetailEditor = new PokemonDetailEditor(
            instances.battleStateManager
        );
        instances.realtimeAnalysis = new RealtimeAnalysis(
            instances.battleStateManager,
            instances.predictionManager
        );
        instances.partySaver = new PartySaver(
            instances.battleStateManager,
            instances.pokemonDetailEditor
        );
        instances.realtimeAnalysis.setPartySaver(instances.partySaver);
        
        // フォーム初期化
        initFormSelects(instances.pokemonDetailEditor);
        
        // イベント委譲
        setupEventDelegation();
        
    } catch (error) {
        console.error('アプリケーション初期化エラー:', error);
        showErrorMessage('アプリケーションの初期化に失敗しました');
    }
});

function setupEventDelegation() {
    document.addEventListener('click', (e) => {
        const itemIcon = e.target.closest('.item-icon');
        if (itemIcon) {
            itemIcon.classList.toggle('grayscale');
            return;
        }
        
        const teraIcon = e.target.closest('.tera-type-icon');
        if (teraIcon) {
            teraIcon.classList.toggle('terastallized-effect');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // パネルの定義を統一
    const panels = {
        left: { element: document.getElementById('left-panel'), toggleBtn: document.getElementById('toggle-left'), type: 'side', icon: { open: '&lt;', closed: '&gt;' }, initialOpen: false },
        right: { element: document.getElementById('right-panel'), toggleBtn: document.getElementById('toggle-right'), type: 'side', icon: { open: '&gt;', closed: '&lt;' }, initialOpen: false },
        topLeft: { element: document.getElementById('top-left-panel'), toggleBtn: document.getElementById('toggle-top-left'), closeBtn: document.getElementById('close-top-left'), type: 'overlay', initialOpen: false },
        topRight: { element: document.getElementById('top-right-panel'), toggleBtn: document.getElementById('toggle-top-right'), closeBtn: document.getElementById('close-top-right'), type: 'overlay', initialOpen: false },
        bottomRight: { element: document.getElementById('bottom-right-panel'), toggleBtn: document.getElementById('toggle-bottom-right'), closeBtn: document.getElementById('close-bottom-right'), type: 'overlay', initialOpen: false },
        command: { 
            element: document.getElementById('command-content'), 
            toggleBtn: document.getElementById('toggle-bottom-left'), 
            type: 'command', 
            initialOpen: true // コマンドパネルは初期で開いている
        },
    };

    /**
     * パネルの開閉を切り替える汎用関数。すべてのパネルタイプに対応。
     * @param {Object} panelData - パネル情報
     * @param {boolean} [forceState] - 状態を強制 (true: 開く, false: 閉じる)。未定義の場合はトグル。
     */
    function togglePanel(panelData, forceState) {
        const { element, toggleBtn, type } = panelData;
        let isOpen;

        // コマンドパネルは初期状態が 'open' なので、トグル動作を反転させる必要がある
        if (type === 'command' && forceState === undefined) {
            isOpen = !element.classList.contains('open');
        } else if (forceState !== undefined) {
            isOpen = forceState;
        } else {
            // side/overlayパネルは初期状態が 'closed' なので、通常トグル
            isOpen = !element.classList.contains('open');
        }

        // 1. クラスのトグル
        element.classList.toggle('open', isOpen);
        
        // 2. 状態に応じたUIの更新
        
        // A. 左右パーティパネル (矢印更新)
        if (type === 'side' && toggleBtn) {
            toggleBtn.innerHTML = isOpen ? panelData.icon.open : panelData.icon.closed;
        }
        
        // B. オーバーレイ/コマンドパネル (アイコン/色/高さ更新)
        if (type === 'overlay' || type === 'command') {
            if (toggleBtn) {
                const icon = toggleBtn.querySelector('i');
                const isCommand = type === 'command';

                if (isOpen) {
                    toggleBtn.classList.add('bg-warning', 'text-dark');
                    toggleBtn.classList.remove('bg-secondary', 'text-light');
                    
                    if (isCommand) {
                        // コマンドパネルは高さを動的に設定
                        // 一度クラスを追加してからscrollHeightを取得しないと正確な値にならない場合があるため、遅延実行
                        setTimeout(() => {
                            element.style.maxHeight = element.scrollHeight + "px";
                        }, 0); 
                        element.style.opacity = '1';
                        element.style.overflow = 'visible';
                        icon.classList.remove('bi-joystick');
                        icon.classList.add('bi-joystick-fill');
                    }
                } else {
                    toggleBtn.classList.remove('bg-warning', 'text-dark');
                    toggleBtn.classList.add('bg-secondary', 'text-light');
                    
                    if (isCommand) {
                        // コマンドパネルは高さを0に設定
                        element.style.maxHeight = '0';
                        element.style.opacity = '0';
                        element.style.overflow = 'hidden';
                        icon.classList.add('bi-joystick');
                        icon.classList.remove('bi-joystick-fill');
                    }
                }
            }
        }
        
        if (toggleBtn) {
            toggleBtn.setAttribute('aria-expanded', isOpen);
        }
    }
    
    // --- 初期状態設定とイベントリスナー設定 ---
    Object.values(panels).forEach(p => {
        // 初期状態の反映（initialOpen=trueのパネルを開き、UIを同期）
        if (p.initialOpen) {
            // 初期化時はアニメーションなしで状態を設定するため forceState=true を使用
            togglePanel(p, true);
        } else if (p.type === 'command') {
            // コマンドパネルが initialOpen: false だった場合の初期設定
            togglePanel(p, false);
        }

        // イベントリスナー設定
        if (p.toggleBtn) {
            p.toggleBtn.addEventListener('click', () => togglePanel(p));
        }
        // クローズボタンは明示的に閉じる (forceState: false)
        if (p.closeBtn) {
            p.closeBtn.addEventListener('click', () => togglePanel(p, false));
        }
    });

});