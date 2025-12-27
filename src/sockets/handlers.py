from flask import current_app
from flask_socketio import emit
from threading import Lock

from src.workers.capture import camera_capture_worker

# スレッド起動用のロック（モジュールレベル）
_thread_start_lock = Lock()

def register_socket_handlers(socketio):
    """
    SocketIOのイベントハンドラを登録します。
    """

    @socketio.on('connect')
    def connect():
        print("Client connected")
        # サーバー再起動時などに意図せず残っているスレッドを停止させる
        _cleanup_threads()
        emit('my_response', {'data': 'Connected'})

    @socketio.on('start_camera')
    def start_camera(data):
        """クライアントからの要求でカメラキャプチャとストリームを開始する (OCRは開始しない)"""
        with _thread_start_lock:
            if _is_any_thread_running():
                print("既に何らかの解析スレッドが実行中です。")
                emit('analysis_stopped', {'error': '他の解析が実行中です。先に停止してください。'})
                return

            print("カメラストリームの開始を要求されました。")
            app_state = current_app.state
            app_state.background_thread_stop_event.clear()
            
            camera_index = data.get('camera_index', 0)
            app_state.capture_thread = socketio.start_background_task(
                target=camera_capture_worker,
                socketio=socketio,
                camera_index=camera_index,
                state=app_state
            )

            video_feed_url = f'/camera_feed?camera_index={camera_index}'
            emit('camera_started', {'video_feed_url': video_feed_url, 'ocr_started': False})

    @socketio.on('start_ocr')
    def start_ocr(battle_state, battle_id):
        """クライアントからの要求でOCR処理のみを開始する"""
        with _thread_start_lock:
            # OCRスレッドが既に実行中かチェック
            if current_app.state.ocr_thread and current_app.state.ocr_thread.is_alive():
                print("既にOCR処理が実行中です。")
                emit('ocr_error', {'error': 'OCR処理が既に実行中です。'})
                return
            
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
        with _thread_start_lock:
            # OCRスレッドが既に実行中かチェック
            if current_app.state.ocr_thread and current_app.state.ocr_thread.is_alive():
                print("既にOCR処理が実行中です。")
                emit('ocr_error', {'error': 'OCR処理が既に実行中です。'})
                return

            app_state = current_app.state
            tesseract_path = current_app.config.get('TESSERACT_PATH')

            # shared_game_stateを更新（ユーザー入力内容を反映）
            with app_state.game_state_lock:
                app_state.shared_game_state["battle_state"] = battle_state

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
        with _thread_start_lock:
            print("解析の停止を要求されました。")
            current_app.state.background_thread_stop_event.set()

            # スレッドの終了を待つ（タイムアウト付き）
            if current_app.state.capture_thread:
                current_app.state.capture_thread.join(timeout=5.0)
                current_app.state.capture_thread = None
            if current_app.state.ocr_thread:
                current_app.state.ocr_thread.join(timeout=5.0)
                current_app.state.ocr_thread = None

            socketio.emit('analysis_stopped')

    @socketio.on('disconnect')
    def disconnect():
        print('Client disconnected')

    # ヘルパー関数
    def _is_any_thread_running():
        """いずれかのスレッドが実行中かチェック"""
        app_state = current_app.state
        return (
            (app_state.capture_thread and app_state.capture_thread.is_alive()) or
            (app_state.ocr_thread and app_state.ocr_thread.is_alive())
        )

    def _cleanup_threads():
        """既存のスレッドをクリーンアップ"""
        app_state = current_app.state
        if app_state.capture_thread or app_state.ocr_thread:
            app_state.background_thread_stop_event.set()
            if app_state.capture_thread:
                app_state.capture_thread.join(timeout=2.0)
            if app_state.ocr_thread:
                app_state.ocr_thread.join(timeout=2.0)
            app_state.capture_thread = None
            app_state.ocr_thread = None

    def ocr_starter_with_context(app, socketio, state, tesseract_path, battle_state, battle_id):
        """アプリケーションコンテキスト付きでOCRワーカーを起動"""
        try:
            with app.app_context():
                from src.workers.ocr import ocr_start
                ocr_start(socketio, state, tesseract_path, battle_state, battle_id)
        finally:
            # スレッド終了時にクリア
            state.ocr_thread = None

    def ocr_ocr_resumer_with_context(app, socketio, state, tesseract_path, battle_state):
        """アプリケーションコンテキスト付きでOCRワーカーを起動"""
        try:
            with app.app_context():
                from src.workers.ocr import ocr_resume
                ocr_resume(socketio, state, battle_state)
        finally:
            # スレッド終了時にクリア
            state.ocr_thread = None