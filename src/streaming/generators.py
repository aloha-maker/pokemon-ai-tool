import time
import cv2
import os
from src.core.capture import ScreenCapturer
from src import state

# app.pyからsocketioインスタンスをインポートすると循環参照になるため、
# ここではtime.sleep()を使用する。
# 高負荷環境で問題になる場合は、socketioインスタンスをDIするなどの工夫が必要。

def video_stream_generator(window_title: str):
    """画面キャプチャを行い、M-JPEGストリームのフレームを生成するジェネレータ"""
    print(f"ビデオストリームを開始します。対象: {window_title}")
    capturer = ScreenCapturer(window_title)
    if not capturer._find_window():
        print(f"警告: ウィンドウ '{window_title}' が見つかりません。ストリームを開始できません。")
        return

    while not state.background_thread_stop_event.is_set():
        frame = capturer.capture_frame()
        if frame is None:
            print("ビデオストリームのフレーム取得に失敗しました。")
            time.sleep(1)
            continue

        frame = cv2.resize(frame, (1280, 720))
        is_success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not is_success:
            continue
        
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(1/30)
    
    print("ビデオストリームを停止しました。")

def camera_stream_generator(camera_index=0):
    """ワーカーが保存した最新のフレーム画像を読み込み、M-JPEGストリームとして生成するジェネレータ"""
    print(f"ファイルベースのカメラストリームを開始します。")
    latest_frame_path = 'static/captures/latest_frame.jpg'

    while not state.background_thread_stop_event.is_set():
        if os.path.exists(latest_frame_path):
            try:
                with open(latest_frame_path, 'rb') as f:
                    frame_bytes = f.read()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except IOError as e:
                print(f"フレーム画像の読み込みに失敗しました: {e}")
                time.sleep(1)
        else:
            time.sleep(0.5)

        time.sleep(1/30)
