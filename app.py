# C:\pokemon-ai-tool\app.py
import os
from flask import Flask
from flask_socketio import SocketIO
from config import config

# 拡張機能の初期化
from src.extensions import executor

# ルート(Blueprint)のインポート
from src.routes.views import views_bp
from src.routes.streaming import streaming_bp
from src.routes.api.ai import ai_bp
from src.routes.api.battle import battle_bp
from src.routes.api.capture import capture_bp
from src.routes.api.party import party_bp
from src.routes.api.video import video_bp
from src.routes.api.roi import roi_bp
from src.routes.api.master import master_bp
from src.routes.api.trained_pokemon import trained_pokemon_bp
from src.routes.api.dashboard import dashboard_bp
from src.routes.api.database import database_bp

# SocketIOハンドラのインポート
from src.sockets.handlers import register_socket_handlers
from src.core.ocr_ import PokemonRecognizer

def create_app():
    """ Flaskアプリケーションを生成して返す (Application Factory パターン) """
    app = Flask(__name__, instance_relative_config=True)

    # --- 環境変数から設定を読み込む ---
    config_name = os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])

    # --- ディレクトリ設定 ---
    # instanceフォルダやstatic/capturesフォルダの存在を確認・作成
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'captures'), exist_ok=True)
    os.makedirs('.img', exist_ok=True)
    os.makedirs('videos', exist_ok=True)

    # --- 拡張機能の初期化 ---
    app.pokemon_recognizer = PokemonRecognizer(threshold=0.8) # ★ 追加
    executor.init_app(app)
    socketio = SocketIO(app)

    # --- Blueprintの登録 ---
    app.register_blueprint(views_bp)
    app.register_blueprint(streaming_bp)
    # API Blueprints
    app.register_blueprint(ai_bp)
    app.register_blueprint(battle_bp)
    app.register_blueprint(capture_bp)
    app.register_blueprint(party_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(roi_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(trained_pokemon_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(database_bp)

    # --- SocketIOハンドラの登録 ---
    register_socket_handlers(socketio)

    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    # debugフラグやhost, portはconfigから読み込まれるか、runのデフォルト値が使われる
    socketio.run(app)