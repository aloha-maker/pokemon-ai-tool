from flask import current_app
from flask_socketio import emit
from urllib.parse import quote

from src.workers.capture import window_capture_worker, camera_capture_worker
from src.workers.ocr import ocr_worker
from src.ai.predictor import ActionAIModel

def register_socket_handlers(socketio):
    """
    SocketIOのイベントハンドラを登録します。
    """

    @socketio.on('connect')
    def connect():
        print("Client connected")
        # サーバー再起動時などに意図せず残っているスレッドを停止させる
        if current_app.state.capture_thread or current_app.state.ocr_thread:
            current_app.state.background_thread_stop_event.set()
            current_app.state.capture_thread = None
            current_app.state.ocr_thread = None
        emit('my_response', {'data': 'Connected'})

    @socketio.on('start_analysis')
    def start_analysis(data):
        """クライアントからの要求でウィンドウキャプチャとOCRを開始する"""
        window_title = data.get('window_title')

        if not window_title:
            emit('analysis_stopped', {'error': 'ウィンドウが選択されていません。'})
            return

        if current_app.state.capture_thread and current_app.state.capture_thread.is_alive() or current_app.state.ocr_thread and current_app.state.ocr_thread.is_alive():
            print("既に何らかの解析スレッドが実行中です。")
            emit('analysis_stopped', {'error': '他の解析が実行中です。先に停止してください。'})
            return

        print(f"ウィンドウ解析の開始を要求されました。対象: {window_title}")
        app_state = current_app.state
        app_state.background_thread_stop_event.clear()
        
        app_state.capture_thread = socketio.start_background_task(target=window_capture_worker, socketio=socketio, window_title=window_title, state=app_state)
        tesseract_path = current_app.config.get('TESSERACT_PATH')
        app_state.ocr_thread = socketio.start_background_task(target=ocr_worker, socketio=socketio, state=app_state, tesseract_path=tesseract_path)
        
        video_feed_url = f'/video_feed?window_title={quote(window_title)}'
        emit('analysis_started', {'video_feed_url': video_feed_url, 'ocr_started': True})

    @socketio.on('start_camera')
    def start_camera(data):
        """クライアントからの要求でカメラキャプチャとストリームを開始する (OCRは開始しない)"""
        if current_app.state.capture_thread and current_app.state.capture_thread.is_alive() or current_app.state.ocr_thread and current_app.state.ocr_thread.is_alive():
            print("既に何らかの解析スレッドが実行中です。")
            emit('analysis_stopped', {'error': '他の解析が実行中です。先に停止してください。'})
            return

        print("カメラストリームの開始を要求されました。")
        app_state = current_app.state
        app_state.background_thread_stop_event.clear()
        
        camera_index = data.get('camera_index', 0)
        app_state.capture_thread = socketio.start_background_task(target=camera_capture_worker, socketio=socketio, camera_index=camera_index, state=app_state)

        video_feed_url = f'/camera_feed?camera_index={camera_index}'
        emit('camera_started', {'video_feed_url': video_feed_url, 'ocr_started': False})

    @socketio.on('start_ocr')
    def start_ocr(data):
        """クライアントからの要求でOCR処理のみを開始する"""
        if current_app.state.ocr_thread and current_app.state.ocr_thread.is_alive():
            print("既にOCRスレッドは実行中です。")
            return
        if not current_app.state.capture_thread or not current_app.state.capture_thread.is_alive():
            print("OCR開始要求がありましたが、キャプチャが実行されていません。")
            emit('analysis_stopped', {'error': 'OCRを開始するには、先にウィンドウかカメラの読み込みを開始してください。'})
            return
        
        print("OCR処理の開始を要求されました。")
        app_state = current_app.state
        # background_thread_stop_event はキャプチャ開始時にクリアされているはず
        tesseract_path = current_app.config.get('TESSERACT_PATH')
        app_state.ocr_thread = socketio.start_background_task(
            target=ocr_worker, 
            socketio=socketio, 
            state=app_state, 
            tesseract_path=tesseract_path,
            battle_data=data
        )
        emit('ocr_started')

    @socketio.on('stop_analysis')
    def stop_analysis(data=None):
        """クライアントからの要求で全ての解析スレッドを停止する"""
        print("解析の停止を要求されました。")
        current_app.state.background_thread_stop_event.set()

        # スレッドの終了を待つ（任意、タイムアウトを設定することも可能）
        if current_app.state.capture_thread:
            current_app.state.capture_thread.join()
            current_app.state.capture_thread = None
        if current_app.state.ocr_thread:
            current_app.state.ocr_thread.join()
            current_app.state.ocr_thread = None

        socketio.emit('analysis_stopped')


    @socketio.on('disconnect')
    def disconnect():
        print('Client disconnected')
        # Consider stopping the thread if the user disconnects
        # current_app.state.background_thread_stop_event.set()

    @socketio.on('get_suggestion')
    def handle_get_suggestion(json_data):
        """
        クライアントからの要求に応じて、最新の盤面情報からAIの提案を生成する
        """
        with current_app.state.game_state_lock:
            battle_state = current_app.state.shared_game_state["battle_state"]
        
        if battle_state:
            # AIモデルで行動を予測
            model = ActionAIModel(app_state=current_app.state)
            recommendation = model.predict_action(battle_state)
            del model # DB接続を閉じる

            # 結果をクライアントに送信
            emit('suggestion_update', recommendation)
        else:
            emit('suggestion_update', {"action": "待機", "reason": "盤面情報を取得中です..."})
