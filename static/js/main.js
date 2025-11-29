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