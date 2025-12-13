# C:\pokemon-ai-tool\app.py
import os
from flask import Flask, jsonify
from flask_socketio import SocketIO
from config import config


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

# SocketIOハンドラのインポート
from src.sockets.handlers import register_socket_handlers
from src.extensions import executor, db
from src.core.ocr_ import PokemonRecognizer

import logging

def create_app(config_name=None):
    """ Flaskアプリケーションを生成して返す (Application Factory パターン) """
    app = Flask(__name__, instance_relative_config=True)

    # --- 環境変数から設定を読み込む ---
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])

    # --- ロギング設定 ---
    if not app.debug:
        logging.basicConfig(level=logging.INFO, filename='production.log',
                            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

    # --- グローバルエラーハンドラ ---
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """予期せぬ例外を捕捉するグローバルハンドラ"""
        logging.exception(f"An unexpected error occurred: {e}")
        return jsonify({"error": "サーバー内部で予期せぬエラーが発生しました。"}), 500

    # --- ディレクトリ設定 ---
    # instanceフォルダやstatic/capturesフォルダの存在を確認・作成
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'captures'), exist_ok=True)
    os.makedirs('.img', exist_ok=True)
    os.makedirs('videos', exist_ok=True)

    # --- 状態管理クラスの初期化 ---
    from src.core.app_state import AppState
    app.state = AppState()

    # --- 拡張機能の初期化 ---
    db.init_app(app)
    app.pokemon_recognizer = PokemonRecognizer(threshold=0.8) # ★ 追加
    executor.init_app(app)
    socketio = SocketIO(app)    

    # --- favicon.ico のリクエストを処理 ---
    @app.route('/favicon.ico')
    def favicon():
        return '', 204

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

    # --- SocketIOハンドラの登録 ---
    register_socket_handlers(socketio)

    # --- アプリケーションコンテキスト内でテーブルを作成 ---
    with app.app_context():
        try:            
            # データベースファイルの存在を確認
            db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            if db_path and not os.path.exists(db_path):
                print(f"データベースファイルを作成: {db_path}")
            
            # テーブルを作成
            db.create_all()
            print("データベーステーブルが初期化されました")
            
        except Exception as e:
            print(f"データベース初期化エラー: {e}")
            # エラーをログに記録するが、アプリケーションは続行
            logging.exception("データベース初期化中にエラーが発生しました")

    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, host='0.0.0.0', port=8000)