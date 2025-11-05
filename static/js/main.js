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

document.addEventListener('DOMContentLoaded', () => {
    // 各機能モジュールの初期化
    new DashboardManager();
    new PartyGenerator();
    new PredictionManager();
    const realtimeAnalysis = new RealtimeAnalysis();
    new VideoAnalysis();
    new ROIEditor();
    new TrainedPokemonManager();
    new PartyManagement();
    new Calculator();
    new Simulator();
    const pokemonDetailEditor = new PokemonDetailEditor();
    new PartySaver(realtimeAnalysis, pokemonDetailEditor);
    const partySaver = new PartySaver(realtimeAnalysis, pokemonDetailEditor);
    
    // フォーム選択肢の初期化はボタンクリック時に行う
    // initFormSelects();

    // RealtimeAnalysisにPartySaverを設定
    realtimeAnalysis.setPartySaver(partySaver);

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
            icon.classList.toggle('terastallized-effect');
        });
    });
});