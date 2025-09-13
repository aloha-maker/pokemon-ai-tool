import mss
import numpy as np
import pygetwindow as gw

class ScreenCapturer:
    """
    指定されたウィンドウの画面をキャプチャするクラス。
    """
    def __init__(self, window_title):
        """
        Args:
            window_title (str): キャプチャ対象のウィンドウタイトル。
        """
        self.window_title = window_title
        self.sct = mss.mss()
        self.target_window = None

    def _find_window(self):
        """
        指定されたタイトルのウィンドウを検索し、情報を更新する。
        """
        try:
            # ウィンドウタイトルに部分一致するものを取得
            windows = gw.getWindowsWithTitle(self.window_title)
            if not windows:
                print(f"警告: ウィンドウ '{self.window_title}' が見つかりません。")
                self.target_window = None
                return False
            # 最初のウィンドウを対象とする
            self.target_window = windows[0]
            return True
        except Exception as e:
            print(f"ウィンドウ検索中にエラーが発生しました: {e}")
            self.target_window = None
            return False

    def capture_frame(self):
        """
        対象ウィンドウの現在のフレームをキャプチャする。

        Returns:
            np.ndarray: キャプチャしたフレームのNumPy配列 (BGR形式)。
                        ウィンドウが見つからない場合は None を返す。
        """
        if not self._find_window() or not self.target_window:
            return None

        # ウィンドウの位置とサイズを取得
        win = self.target_window
        
        # ウィンドウが最小化されている場合はキャプチャしない
        if win.isMinimized:
            print("警告: ウィンドウが最小化されています。")
            return None

        monitor = {
            "top": win.top,
            "left": win.left,
            "width": win.width,
            "height": win.height,
        }

        # 画面をキャプチャ
        sct_img = self.sct.grab(monitor)

        # mssのBGRA形式からNumPyのBGR形式に変換
        img = np.array(sct_img)
        img = img[:, :, :3] # アルファチャンネルを削除

        return img
