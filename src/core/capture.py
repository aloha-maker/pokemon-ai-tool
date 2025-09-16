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
        完全一致するタイトルを持つウィンドウを優先する。
        """
        try:
            all_windows = gw.getAllWindows()
            target_win = None
            
            # まずタイトルが完全に一致するものを探す
            for win in all_windows:
                if win.title == self.window_title:
                    target_win = win
                    break
            
            if target_win:
                self.target_window = target_win
                return True
            else:
                # 完全一致がない場合、警告を出しつつ部分一致を試みる（フォールバック）
                windows = gw.getWindowsWithTitle(self.window_title)
                if not windows:
                    print(f"警告: ウィンドウ '{self.window_title}' が見つかりません。")
                    self.target_window = None
                    return False
                
                print(f"警告: ウィンドウ名 '{self.window_title}' に完全一致するウィンドウが見つかりませんでした。部分一致する '{windows[0].title}' を対象とします。")
                self.target_window = windows[0]
                return True

        except Exception as e:
            print(f"ウィンドウ検索中にエラーが発生しました: {e}")
            self.target_window = None
            return False

    def capture_frame(self, region: tuple[int, int, int, int] | None = None):
        """
        対象ウィンドウの現在のフレームをキャプチャする。
        領域を指定して、その部分だけを切り出すことも可能。

        Args:
            region (tuple[int, int, int, int] | None, optional):
                キャプチャする領域を(left, top, width, height)で指定。
                ウィンドウ左上からの相対座標。 Defaults to None (ウィンドウ全体).

        Returns:
            np.ndarray: キャプチャしたフレームのNumPy配列 (BGR形式)。
                        ウィンドウが見つからない、または領域が不正な場合は None を返す。
        """
        if not self._find_window() or not self.target_window:
            return None

        win = self.target_window
        if win.isMinimized:
            print("警告: ウィンドウが最小化されています。")
            return None

        if region:
            # 領域指定がある場合
            if not (isinstance(region, (list, tuple)) and len(region) == 4):
                print("エラー: regionは (left, top, width, height) の4要素で指定してください。")
                return None
            
            monitor = {
                "top": win.top + region[1],
                "left": win.left + region[0],
                "width": region[2],
                "height": region[3],
            }
        else:
            # 領域指定がない場合はウィンドウ全体
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
        img = img[:, :, :3]  # アルファチャンネルを削除

        return img
