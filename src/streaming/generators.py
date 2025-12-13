import time
# import cv2
import os
from src.core.capture import ScreenCapturer

# app.pyからsocketioインスタンスをインポートすると循環参照になるため、
# ここではtime.sleep()を使用する。
# 高負荷環境で問題になる場合は、socketioインスタンスをDIするなどの工夫が必要。

# def video_stream_generator(window_title: str, stop_event):
#     """画面キャプチャを行い、M-JPEGストリームのフレームを生成するジェネレータ"""
#     print(f"ビデオストリームを開始します。対象: {window_title}")
#     capturer = ScreenCapturer(window_title)
#     if not capturer._find_window():
#         print(f"警告: ウィンドウ '{window_title}' が見つかりません。ストリームを開始できません。")
#         return

#     while not stop_event.is_set():
#         frame = capturer.capture_frame()
#         if frame is None:
#             print("ビデオストリームのフレーム取得に失敗しました。")
#             time.sleep(1)
#             continue

#         frame = cv2.resize(frame, (1280, 720))
#         is_success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
#         if not is_success:
#             continue
        
#         frame_bytes = buffer.tobytes()
        
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
#         time.sleep(1/30)
    
#     print("ビデオストリームを停止しました。")

def camera_stream_generator(camera_index, state):
    """ワーカーがメモリに保存した最新のフレームを読み込み、M-JPEGストリームとして生成するジェネレータ"""
    print(f"メモリベースのカメラストリームを開始します。")

    while not state.background_thread_stop_event.is_set():
        frame_bytes = None
        with state.frame_lock:
            if state.latest_frame_bytes:
                frame_bytes = state.latest_frame_bytes
        
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # フレームがまだない場合は少し待つ
            time.sleep(0.1)

        time.sleep(1/60) # フレームレートを60fpsに近づける
