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
import { ItemEditor } from './modules/itemEditor.js';
import { initFormSelects } from './modules/formHelpers.js';

document.addEventListener('DOMContentLoaded', () => {
    // 各機能モジュールの初期化
    new DashboardManager();
    new PartyGenerator();
    new PredictionManager();
    new RealtimeAnalysis();
    new VideoAnalysis();
    new ROIEditor();
    new TrainedPokemonManager();
    new PartyManagement();
    new Calculator();
    new Simulator();
    new ItemEditor();
    
    // フォーム選択肢の初期化
    initFormSelects();

    // 持ち物アイコンのクリックイベント
    document.querySelectorAll('.item-icon').forEach(icon => {
        icon.style.cursor = 'pointer'; // クリック可能であることを示すカーソル
        icon.addEventListener('click', () => {
            icon.classList.toggle('grayscale');
        });
    });

    // テラスタイプアイコンのクリックイベント
    document.querySelectorAll('.tera-type-icon').forEach(icon => {
        icon.style.cursor = 'pointer'; // クリック可能であることを示すカーソル
        icon.addEventListener('click', () => {
            icon.classList.toggle('grayscale');
        });
    });
});