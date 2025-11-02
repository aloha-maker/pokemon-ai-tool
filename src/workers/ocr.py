import cv2
import os
import time
import numpy as np
from src.core.ocr.ocr_processor import OCRProcessor
from src.core.ocr.name_corrector import PokemonNameCorrector, AbilityNameCorrector
from src.core.ocr import config  # configモジュールをインポート

from src.schemas.pokemon_battle.battle_log import BattleLog
from src.models.raw_battle_event_model import RawBattleEventModel

def ocr_worker(socketio, state, tesseract_path):
    """
    バックグラウンドでOCRを定期的に実行するワーカー
    'static/captures/latest_frame.jpg' を監視して処理を行う
    OCRProcessorを使用して高度なフェーズ管理とROI処理を行う
    """
    print("OCRワーカーを開始します。")
    
    # 名前補正クラスとOCRプロセッサーの初期化（video.pyと同様）
    try:
        pokemon_corrector = PokemonNameCorrector(config.POKEMON_MASTER_PATH)
        ability_corrector = AbilityNameCorrector(config.ABILITY_MASTER_PATH)
        ocr_processor = OCRProcessor(pokemon_corrector, ability_corrector, tesseract_path=tesseract_path)
        battle_log = BattleLog(
            battle_id='todo', # TODO クライアントからもってくる
            battle_date='todo',
            season='todo',
            regulation='todo',
            battle_format='シングル',
            my_rank=0,
            opponent_rank=0,
        )
        print("✅ OCRProcessorの初期化が完了しました")
    except Exception as e:
        print(f"❌ OCRProcessorの初期化に失敗しました: {e}")
        return

    frame_count = 0
    
    while not state.background_thread_stop_event.is_set():
        frame_bytes = None
        with state.frame_lock:
            if state.latest_frame_bytes:
                frame_bytes = state.latest_frame_bytes

        if frame_bytes:
            try:
                np_arr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if frame is not None:
                    # OCR処理には常に1920x1080の解像度を期待
                    frame_resized = cv2.resize(frame, (1920, 1080))
                    
                    # OCRProcessorを使用してゲーム状態を解析
                    height, width = frame_resized.shape[:2]
                    
                    # フェーズ検出
                    phase_manager = ocr_processor.detect_phase(frame_resized, width, height)
                    current_phase_info = ocr_processor.get_current_phase_info()
                    
                    # フェーズに応じたROI処理を実行
                    processed_count = ocr_processor.process_phase_rois(
                        frame_resized, 
                        "realtime_capture",  # ビデオ名
                        frame_count,  # フレームインデックス
                        "realtime",  # 短いハッシュ
                        width, height
                    )
                    
                    # 解析結果を取得
                    current_state, battle_log = _extract_state_from_ocr_processor(ocr_processor, current_phase_info, battle_log, frame_count)
                    
                    with state.game_state_lock:
                        state.shared_game_state["state"] = current_state
                        state.shared_game_state["last_updated"] = time.time()
                        state.shared_game_state["phase_info"] = current_phase_info
                        state.shared_game_state["battle_log"] = battle_log
                        state.shared_game_state["battle_state"] = None
                    
                    # クライアントに状態更新を通知
                    socketio.emit('ocr_update', {
                        'state': current_state,
                        'phase_info': current_phase_info,
                        'processed_count': processed_count,
                        'battle_log' : battle_log.to_dict(),
                        'battle_state' : None
                    })
                    
                    if frame_count % 10 == 0:  # 10フレームごとにログ出力
                        print(f"📊 フレーム {frame_count}: フェーズ={current_phase_info['current_phase']}, 処理ROI数={processed_count}")
                    
                    frame_count += 1
                    
                else:
                    print("❌ OCRワーカー: フレームの読み込みに失敗しました。")
            except Exception as e:
                print(f"❌ OCRワーカーでエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()
        else:
            # キャプチャが開始されるまで待機（初回のみメッセージ表示）
            if frame_count == 0:
                print("⏳ OCRワーカー: latest_frame.jpgを待機中...")
            pass

        time.sleep(0.5)  # 0.5秒間隔でチェック（よりリアルタイムに）

    print("🛑 OCRワーカーを停止しました。")

def _extract_state_from_ocr_processor(ocr_processor, phase_info, battle_log, frame_count):
    """
    OCRProcessorの内部状態からゲーム状態を抽出する
    """
    current_state = {
        'game_text': '',
        'my_pokemon_1_name': '',
        'my_pokemon_1_hp_percent': None,
        'opponent_pokemon_1_name': '',
        'opponent_pokemon_1_hp_percent': None,
        'phase': phase_info['current_phase'],
        'battle_sub_phase': phase_info.get('battle_sub_phase', ''),
        'battle_id': '',
        'triggered_ability': '',
        'field_effects': None,
        'raw_ocr_result': {}
    }
    
    try:
        # 自分のポケモン名
        if hasattr(ocr_processor, 'last_my_pokemon_name') and ocr_processor.last_my_pokemon_name:
            current_state['my_pokemon_1_name'] = ocr_processor.last_my_pokemon_name
        
        # 相手のポケモン名  
        if hasattr(ocr_processor, 'last_opponent_pokemon_name') and ocr_processor.last_opponent_pokemon_name:
            current_state['opponent_pokemon_1_name'] = ocr_processor.last_opponent_pokemon_name
            
        # バトルID
        if hasattr(ocr_processor, 'current_battle_id') and ocr_processor.current_battle_id:
            current_state['battle_id'] = ocr_processor.current_battle_id
            
        # OCRプロセッサーから直接OCR結果を取得
        raw_results = ocr_processor.ocr_processor.last_ocr_results
        current_state['raw_ocr_result'] = raw_results
        
        # ライブコメントなどのテキスト情報を抽出
        game_text_parts = []
        for roi_name in ['live_comment_row1', 'live_comment_row2']:
            if roi_name in raw_results and raw_results[roi_name].get('text'):
                game_text_parts.append(raw_results[roi_name]['text'])
        
        if game_text_parts:
            current_state['game_text'] = ' '.join(game_text_parts)
            
        # 特性情報を抽出
        ability_parts = []
        for roi_name in ['my_tokusei_row1', 'my_tokusei_row2', 'your_tokusei_row1', 'your_tokusei_row2']:
            if roi_name in raw_results and raw_results[roi_name].get('text'):
                ability_parts.append(raw_results[roi_name]['text'])
        
        if ability_parts:
            current_state['triggered_ability'] = ' '.join(ability_parts)

        
        # RawBattleEventModelにセット
        raw_battle_event_model_list = []
        for roi_name, ocr_text in raw_results.items():            
            raw_battle_event_model = RawBattleEventModel(
                        battle_id=battle_log.battle_id,
                        sequence=frame_count,
                        roi_name=roi_name,
                        ocr_text=ocr_text['text'],
                        phase=phase_info['current_phase']
                    )
            raw_battle_event_model_list.append(raw_battle_event_model)
        # battle_logにセット
        battle_log.event = raw_battle_event_model_list

                    
    except Exception as e:
        print(f"⚠️ 状態抽出エラー: {e}")
    
    return current_state, battle_log
