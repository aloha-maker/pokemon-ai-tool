import cv2
import os
import time
from src.core.capture import ScreenCapturer
from src import state

def window_capture_worker(socketio, window_title):
    """ウィンドウキャプチャを行い、latest_frame.jpgを更新するワーカー"""
    print(f"ウィンドウキャプチャワーカーを開始します。対象: {window_title}")
    capturer = ScreenCapturer(window_title)
    if not capturer._find_window():
        print(f"警告: ウィンドウ '{window_title}' が見つかりません。")
        socketio.emit('analysis_stopped', {'error': f'ウィンドウ「{window_title}」が見つかりません。'})
        return

    while not state.background_thread_stop_event.is_set():
        frame = capturer.capture_frame()
        if frame is not None:
            cv2.imwrite('static/captures/latest_frame.jpg', frame)
        else:
            print("ウィンドウキャプチャワーカー: フレーム取得に失敗しました。")
            # ウィンドウが閉じられた可能性
            state.background_thread_stop_event.set()
            socketio.emit('analysis_stopped', {'error': 'キャプチャ対象のウィンドウが閉じられた可能性があります。'})
            break
        time.sleep(1/30) # キャプチャフレームレート
    print("ウィンドウキャプチャワーカーを停止しました。")

def camera_capture_worker(socketio, camera_index):
    """カメラキャプチャを行い、latest_frame.jpgを更新するワーカー"""
    print(f"[Log] カメラキャプチャワーカー開始。デバイス: {camera_index}")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    if not cap.isOpened():
        print(f"警告: カメラデバイス {camera_index} を開けません。")
        socketio.emit('analysis_stopped', {'error': f'カメラデバイス {camera_index} が見つかりません。'})
        return

    while not state.background_thread_stop_event.is_set():
        ret, frame = cap.read()
        if ret:
            is_success, buffer = cv2.imencode(".jpg", frame)
            if is_success:
                tmp_path = 'static/captures/latest_frame.tmp'
                final_path = 'static/captures/latest_frame.jpg'
                with open(tmp_path, 'wb') as f:
                    f.write(buffer)
                try:
                    os.replace(tmp_path, final_path)
                except PermissionError:
                    # The reader thread might have the file open. It's safe to skip.
                    pass
        else:
            print("カメラキャプチャワーカー: フレーム取得に失敗しました。")
            state.background_thread_stop_event.set()
            socketio.emit('analysis_stopped', {'error': 'カメラからの映像取得に失敗しました。'})
            break
        time.sleep(1/30) # キャプチャフレームレート
    
    cap.release()
    print("カメラキャプチャワーカーを停止しました。")
