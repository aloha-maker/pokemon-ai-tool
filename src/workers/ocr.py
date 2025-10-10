import cv2
import os
import time
from src.core.ocr import GameStateParser
from src import state

def ocr_worker(socketio):
    """
    バックグラウンドでOCRを定期的に実行するワーカー（画像ソースに依存しない）
    'static/captures/latest_frame.jpg' を監視して処理を行う
    """
    print("OCRワーカーを開始します。")
    parser = GameStateParser()
    
    while not state.background_thread_stop_event.is_set():
        frame_path = 'static/captures/latest_frame.jpg'
        if os.path.exists(frame_path):
            try:
                frame = cv2.imread(frame_path)
                if frame is not None:
                    # OCR処理には常に1920x1080の解像度を期待
                    frame_resized = cv2.resize(frame, (1920, 1080))
                    current_state = parser.parse_frame(frame_resized)
                    
                    with state.game_state_lock:
                        state.shared_game_state["state"] = current_state
                        state.shared_game_state["last_updated"] = time.time()
                    
                    socketio.emit('ocr_update', {'state': current_state})
                else:
                    print("OCRワーカー: フレームの読み込みに失敗しました。")
            except Exception as e:
                print(f"OCRワーカーでエラーが発生しました: {e}")
        else:
            # print("OCRワーカー: latest_frame.jpgが見つかりません。キャプチャソースがアクティブか確認してください。")
            pass # キャプチャが開始されるまで待機

        time.sleep(1) # OCRの実行頻度を制御
    
    print("OCRワーカーを停止しました。")
