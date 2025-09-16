from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import sqlite3
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

app = Flask(__name__)
socketio = SocketIO(app)

# --- Background OCR and AI Thread ---

# TODO: このウィンドウタイトルは設定ファイルなどから読み込むように変更する
TARGET_WINDOW_TITLE = "mGBA"

# スレッド間で共有するデータ
shared_game_state = {
    "state": None,
    "last_updated": None
}
game_state_lock = threading.Lock()
background_thread_stop_event = threading.Event()

def ocr_and_suggestion_thread():
    """
    バックグラウンドで画面キャプチャ、OCR、AIによる提案を定期的に実行するスレッド
    """
    print("バックグラウンドOCRスレッドを開始します。")
    capturer = ScreenCapturer(TARGET_WINDOW_TITLE)
    parser = GameStateParser()
    
    while not background_thread_stop_event.is_set():
        frame = capturer.capture_frame()
        
        if frame is not None:
            # 1. 盤面情報を抽出
            current_state = parser.parse_frame(frame)
            
            # 2. 共有データを更新
            with game_state_lock:
                shared_game_state["state"] = current_state
                shared_game_state["last_updated"] = time.time()
            
            # 3. フロントエンドにOCR結果を送信 (デバッグ用)
            socketio.emit('ocr_update', {'state': current_state})

        # 2秒待機
        socketio.sleep(2)
    
    print("バックグラウンドOCRスレッドを停止しました。")


@socketio.on('connect')
def connect():
    print("Client connected")
    # 新しいクライアントが接続したときにバックグラウンドスレッドがなければ開始
    global background_thread
    if 'background_thread' not in globals() or not background_thread.is_alive():
        print("バックグラウンドスレッドを開始します。")
        background_thread = socketio.start_background_task(target=ocr_and_suggestion_thread)
    emit('my_response', {'data': 'Connected'})

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

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

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'pokemon_ai.db')

def init_db():
    """Initializes the database and creates the match_history table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            my_party TEXT,
            opponent_party TEXT,
            my_selection TEXT, 
            result TEXT,
            created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
        )
    """
    )
    conn.commit()
    conn.close()

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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO match_history (my_party, opponent_party, my_selection, result) VALUES (?, ?, ?, ?)",
            (
                json.dumps(data['my_party']),
                json.dumps(data['opponent_party']),
                json.dumps(data['my_selection']),
                data['result']
            )
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "対戦履歴を保存しました。"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM match_history ORDER BY created_at DESC LIMIT 50")
        raw_history = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) as total FROM match_history")
        total_matches = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as wins FROM match_history WHERE result = 'win'")
        total_wins = cursor.fetchone()['wins']

        win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

        conn.close()

        return jsonify({
            "raw_history": raw_history,
            "stats": {
                "total_matches": total_matches,
                "total_wins": total_wins,
                "win_rate": round(win_rate, 1)
            }
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

if __name__ == '__main__':
    init_db()
    captures_dir = os.path.join('static', 'captures')
    os.makedirs(captures_dir, exist_ok=True)
    
    # Start the background thread
    # Note: Using Flask's development server with socketio.run will handle threading correctly.
    # For production, a different setup (e.g., Gunicorn + eventlet/gevent) is needed.
    socketio.run(app, debug=True)