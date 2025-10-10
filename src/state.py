import threading

# 動画解析タスクの状態を管理
video_tasks = {}

# バックグラウンドで動作するスレッドを管理
capture_thread = None
ocr_thread = None
background_thread_stop_event = threading.Event()

# OCR結果をスレッド間で共有するためのデータとロック
game_state_lock = threading.Lock()
shared_game_state = {
    "state": None,
    "last_updated": None
}
