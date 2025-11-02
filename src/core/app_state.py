import threading

class AppState:
    """
    アプリケーション全体の実行時状態を管理するクラス。
    グローバル変数を廃し、状態をこのクラスにカプセル化することで、
    スレッドセーフなアクセスとテストの容易性を確保する。
    """
    def __init__(self):
        # 動画解析タスクの状態を管理
        self.video_tasks = {}

        # バックグラウンドで動作するスレッドを管理
        self.capture_thread = None
        self.ocr_thread = None
        self.background_thread_stop_event = threading.Event()

        # OCR結果などをスレッド間で共有するためのデータとロック
        self.game_state_lock = threading.Lock()
        self.shared_game_state = {
            "state": None,
            "last_updated": None
        }

        # カメラフレームをメモリ上で共有するためのデータとロック
        self.frame_lock = threading.Lock()
        self.latest_frame_bytes = None
