from flask import current_app
from flask_socketio import emit
from urllib.parse import quote

from src.workers.capture import camera_capture_worker # window_capture_worker
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
    def start_ocr(battle_state,battle_id):
        """クライアントからの要求でOCR処理のみを開始する"""
        
        print("OCR処理の開始を要求されました。")
        
        app_state = current_app.state
        tesseract_path = current_app.config.get('TESSERACT_PATH')

        # Flaskアプリを取得して渡す
        app = current_app._get_current_object()
        app_state.ocr_thread = socketio.start_background_task(
            target=ocr_starter_with_context,
            app=app,
            socketio=socketio,
            state=app_state,
            tesseract_path=tesseract_path,
            battle_state=battle_state,
            battle_id=battle_id
        )
        emit('ocr_started')
    
    @socketio.on('resume_ocr')
    def resume_ocr(battle_state):
        """ユーザー入力後にOCRを再開する"""
        app_state = current_app.state
        tesseract_path = current_app.config.get('TESSERACT_PATH')

        # shared_game_stateを更新（ユーザー入力内容を反映）
        with app_state.game_state_lock:
            app_state.shared_game_state["battle_state"] = battle_state

        # イベントフラグをリセット
        # app_state.background_thread_stop_event.clear()

        # Flaskアプリを取得して新スレッドを起動
        app = current_app._get_current_object()
        app_state.ocr_thread = socketio.start_background_task(
            target=ocr_ocr_resumer_with_context,
            app=app,
            socketio=socketio,
            state=app_state,
            tesseract_path=tesseract_path,
            battle_state=battle_state
        )

        emit('ocr_resumed', {"message": "OCR再開しました"})

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

    def ocr_starter_with_context(app, socketio, state, tesseract_path, battle_state, battle_id):
        """アプリケーションコンテキスト付きでOCRワーカーを起動"""
        with app.app_context():
            from src.workers.ocr import ocr_start
            ocr_start(socketio, state, tesseract_path, battle_state, battle_id)


    def ocr_ocr_resumer_with_context(app, socketio, state, tesseract_path, battle_state):
        """アプリケーションコンテキスト付きでOCRワーカーを起動"""
        with app.app_context():
            from src.workers.ocr import ocr_resume
            ocr_resume(socketio, state, battle_state)