from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_executor import Executor
import uuid
import json
import os
import time
import threading
import cv2
import pygetwindow
from src.core.capture import ScreenCapturer
from src.ai.party_generator import PartyGenerator
from src.ai.win_rate_predictor import WinRatePredictor
from src.core.ocr import GameStateParser
from src.ai.predictor import ActionAIModel
from src.database.manager import DatabaseManager
from src.core.video_processor import VideoProcessor
from src.ui.routes import api_bp # ★ 追加

app = Flask(__name__)
app.register_blueprint(api_bp) # ★ 追加

socketio = SocketIO(app)
executor = Executor(app)

# --- Video Processing Globals ---
VIDEO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
video_tasks = {}

# --- Background OCR and AI Thread ---

# スレッドを管理するためのグローバル変数
background_thread = None
background_thread_stop_event = threading.Event()
game_state_lock = threading.Lock()
shared_game_state = {
    "state": None,
    "last_updated": None
}

def ocr_and_suggestion_thread(window_title: str):
    """
    バックグラウンドで画面キャプチャ、OCR、AIによる提案を定期的に実行するスレッド
    """
    print(f"バックグラウンドOCRスレッドを開始します。対象: {window_title}")
    capturer = ScreenCapturer(window_title)
    parser = GameStateParser()
    
    if not capturer._find_window():
        print(f"警告: ウィンドウ '{window_title}' が見つかりません。")
        socketio.emit('analysis_stopped', {'error': f"ウィンドウ '{window_title}' が見つかりません。"})
        return

    while not background_thread_stop_event.is_set():
        frame = capturer.capture_frame()
        
        if frame is not None:
            # フレームを1920x1080にリサイズ
            frame = cv2.resize(frame, (1920, 1080))

            # キャプチャした画像をファイルに保存
            captures_dir = os.path.join('static', 'captures')
            # 常に同じファイル名で上書きすることで、ストレージを圧迫しない
            live_capture_path = os.path.join(captures_dir, "live_capture.png")
            cv2.imwrite(live_capture_path, frame)
            # ブラウザがキャッシュしないように、URLにタイムスタンプを付与するための準備
            image_url = f'/{live_capture_path.replace("\\", "/")}'

            current_state = parser.parse_frame(frame)
            with game_state_lock:
                shared_game_state["state"] = current_state
                shared_game_state["last_updated"] = time.time()
            
            socketio.emit('ocr_update', {'state': current_state, 'image_url': image_url})
        else:
            # ウィンドウが閉じた、最小化されたなどの理由でキャプチャできなくなった場合
            print("フレームのキャプチャに失敗しました。スレッドを停止します。")
            socketio.emit('analysis_stopped', {'error': '対象ウィンドウからのキャプチャに失敗しました。'})
            break

        socketio.sleep(2)
    
    print("バックグラウンドOCRスレッドを停止しました。")

@socketio.on('connect')
def connect():
    print("Client connected")
    emit('my_response', {'data': 'Connected'})

@socketio.on('start_analysis')
def start_analysis(data):
    """クライアントからの要求で解析スレッドを開始する"""
    global background_thread
    window_title = data.get('window_title')

    if not window_title:
        emit('analysis_stopped', {'error': 'ウィンドウが選択されていません。'})
        return

    if background_thread and background_thread.is_alive():
        print("既に解析スレッドが実行中です。")
        return

    print(f"解析スレッドの開始を要求されました。対象: {window_title}")
    background_thread_stop_event.clear()
    background_thread = socketio.start_background_task(
        target=ocr_and_suggestion_thread, 
        window_title=window_title
    )
    emit('analysis_started')

@socketio.on('stop_analysis')
def stop_analysis(data=None):
    """クライアントからの要求で解析スレッドを停止する"""
    global background_thread
    print("解析スレッドの停止を要求されました。")
    background_thread_stop_event.set()
    emit('analysis_stopped')


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')
    # Consider stopping the thread if the user disconnects
    # background_thread_stop_event.set()

@socketio.on('get_suggestion')
def handle_get_suggestion(json_data):
    """
    クライアントからの要求に応じて、最新の盤面情報からAIの提案を生成する
    """
    with game_state_lock:
        current_state = shared_game_state["state"]
    
    if current_state:
        # AIモデルで行動を予測
        model = ActionAIModel()
        recommendation = model.predict_action(current_state)
        del model # DB接続を閉じる

        # 結果をクライアントに送信
        emit('suggestion_update', recommendation)
    else:
        emit('suggestion_update', {"action": "待機", "reason": "盤面情報を取得中です..."})


# --- REST API Endpoints ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    my_party = data.get('my_party', [])
    opponent_party = data.get('opponent_party', [])

    if len(my_party) != 6 or len(opponent_party) != 6:
        return jsonify({"error": "パーティはそれぞれ6体入力してください。"}), 400

    predictor = WinRatePredictor()
    result = predictor.predict_best_team(my_party, opponent_party)
    del predictor

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)

@app.route('/generate-party', methods=['POST'])
def generate_party():
    data = request.json
    available_pokemon = data.get('available_pokemon', [])
    concept = data.get('concept', '')

    if not available_pokemon or not concept:
        return jsonify({"error": "使用可能なポケモンと戦術コンセプトを入力してください。"}), 400

    generator = PartyGenerator()
    result = generator.generate(available_pokemon, concept)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)

@app.route('/api/capture', methods=['POST'])
def capture_window():
    data = request.get_json()
    if not data or 'window_title' not in data:
        return jsonify({"error": "window_title is required."} ), 400

    window_title = data['window_title']
    region = data.get('region')

    capturer = ScreenCapturer(window_title)
    
    if not capturer._find_window():
        return jsonify({"error": f"Window '{window_title}' not found."} ), 404

    frame = capturer.capture_frame(region=region)

    if frame is None:
        return jsonify({"error": "Failed to capture frame."} ), 500

    try:
        captures_dir = os.path.join('static', 'captures')
        filename = f"captured_{int(time.time())}.png"
        filepath = os.path.join(captures_dir, filename)
        
        cv2.imwrite(filepath, frame)
        
        return jsonify({
            "message": "Capture successful.",
            "file_path": filepath.replace('\\', '/')
        })
    except Exception as e:
        return jsonify({"error": f"Failed to save image: {str(e)}"} ), 500

@app.route('/api/history/add', methods=['POST'])
def add_history():
    data = request.json
    try:
        with DatabaseManager() as db:
            db.add_battle_log(data)
        return jsonify({"message": "対戦履歴を保存しました。"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        with DatabaseManager() as db:
            raw_history = db.get_battle_history()
            stats = db.get_battle_stats()

        return jsonify({
            "raw_history": raw_history,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ocr_test', methods=['POST'])
def ocr_test():
    data = request.get_json()
    if not data or 'image_path' not in data:
        return jsonify({"error": "image_path is required."}), 400

    image_path = data['image_path']
    if not os.path.exists(image_path):
        return jsonify({"error": f"Image not found at '{image_path}'"}), 404

    try:
        img = cv2.imread(image_path)
        if img is None:
            return jsonify({"error": f"Failed to read image from '{image_path}'"}), 500

        parser = GameStateParser()
        game_state = parser.parse_frame(img)

        return jsonify({
            "message": "OCR process completed.",
            "ocr_results": game_state
        })
    except Exception as e:
        return jsonify({"error": f"An error occurred during OCR processing: {str(e)}"}), 500

@app.route('/api/windows', methods=['GET'])
def get_windows():
    try:
        titles = pygetwindow.getAllTitles()
        window_titles = [title for title in titles if title]
        return jsonify({"windows": window_titles})
    except Exception as e:
        return jsonify({"error": f"Failed to get window titles: {str(e)}"}), 500

# --- Video Analysis API Endpoints ---

@app.route('/api/videos/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    task_id = str(uuid.uuid4())
    filename = f"{task_id}_{file.filename}"
    filepath = os.path.join(VIDEO_DIR, filename)

    try:
        os.makedirs(VIDEO_DIR, exist_ok=True)
        file.save(filepath)
        
        # タスクの状態を初期化
        video_tasks[task_id] = {"status": "PENDING", "result": None, "filename": file.filename}
        
        # バックグラウンドで動画解析を実行
        executor.submit(analyze_video_task, task_id, filepath)

        return jsonify({"message": "Video uploaded successfully. Analysis started.", "task_id": task_id}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/videos/status/<task_id>', methods=['GET'])
def get_video_status(task_id):
    task = video_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

def analyze_video_task(task_id, filepath):
    """バックグラウンドで実行される動画解析タスク"""
    try:
        print(f"[Task {task_id}] Video analysis started for {filepath}")
        video_tasks[task_id]["status"] = "PROCESSING"
        
        # VideoProcessorは、解析結果としてターンデータのdictを返すと想定
        processor = VideoProcessor(filepath)
        turn_data = processor.analyze()

        log_id = None
        with DatabaseManager() as db:
            log_id = db.add_battle_log_from_video(task_id, turn_data)

        video_tasks[task_id]["status"] = "DONE"
        video_tasks[task_id]["result"] = {"log_id": log_id}
        print(f"[Task {task_id}] Video analysis finished. Log ID: {log_id}")

    except Exception as e:
        print(f"[Task {task_id}] Error during video analysis: {e}")
        video_tasks[task_id]["status"] = "ERROR"
        video_tasks[task_id]["result"] = {"error": str(e)}

@app.route('/api/videos/result/<int:log_id>', methods=['GET'])
def get_video_result(log_id):
    """指定されたlog_idの解析結果をデータベースから取得する"""
    try:
        with DatabaseManager() as db:
            log = db.get_battle_log_by_id(log_id)
            if not log:
                return jsonify({"error": "Log not found"}), 404
            return jsonify(log)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ROI Editor API Endpoints ---

ROI_CONFIG_PATH = 'roi_config.json'

@app.route('/api/roi/config', methods=['GET'])
def get_roi_config():
    try:
        if os.path.exists(ROI_CONFIG_PATH):
            with open(ROI_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        else:
            # デフォルトの空のコンフィグを返す
            return jsonify({
                "reference_resolution": {"width": 1280, "height": 720},
                "my_pokemon_name": [0,0,0,0],
                "opponent_pokemon_name": [0,0,0,0],
                "my_pokemon_hp": [0,0,0,0],
                "opponent_pokemon_hp": [0,0,0,0]
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/roi/update', methods=['POST'])
def update_roi_config():
    try:
        new_config = request.json
        with open(ROI_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, indent=4, ensure_ascii=False)
        return jsonify({"message": "ROI configuration updated successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/roi/image_path', methods=['GET'])
def get_roi_image_path():
    # ROI編集に使用する画像のパスを返す
    # リアルタイム解析中の最新画像を利用するのが合理的
    return jsonify({"image_path": "/static/captures/live_capture.png"})

    """育成済みポケモン管理ページを表示する。"""
    return render_template('trained_pokemon_management.html')

if __name__ == '__main__':
    # アプリケーションをデバッグモードで実行
    # host='0.0.0.0' を指定することで、外部からのアクセスを許可する
    app.run(debug=True, host='0.0.0.0', port=5001)
