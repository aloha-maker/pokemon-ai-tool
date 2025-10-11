import cv2
import numpy as np

def get_hp_percentage(image_path: str) -> float:
    """シンプルバージョン（緑・黄・赤すべて対応）"""
    image = cv2.imread(image_path)
    if image is None:
        return 0.0
    
    # 中央の1行だけを分析（ノイズを減らす）
    height, width = image.shape[:2]
    center_row = height // 2
    
    # 中央行をHSV変換
    hsv_row = cv2.cvtColor(image[center_row:center_row+1, :], cv2.COLOR_BGR2HSV)
    hsv_row = hsv_row[0]  # 2次元から1次元に
    
    # すべてのHP色の範囲を定義
    color_ranges = [
        # 緑色
        (np.array([35, 50, 50]), np.array([85, 255, 255])),
        # 黄色
        (np.array([15, 80, 80]), np.array([35, 255, 255])),
        # 赤色（2つの範囲）
        (np.array([0, 50, 50]), np.array([10, 255, 255])),
        (np.array([170, 50, 50]), np.array([180, 255, 255]))
    ]
    
    # HPが存在する位置を検出
    hp_positions = []
    for x in range(width):
        pixel = hsv_row[x]
        
        # すべての色範囲をチェック
        for lower, upper in color_ranges:
            if (lower[0] <= pixel[0] <= upper[0] and
                lower[1] <= pixel[1] <= upper[1] and
                lower[2] <= pixel[2] <= upper[2]):
                hp_positions.append(x)
                break  # いずれかの色に一致したら次のピクセルへ
    
    if not hp_positions:
        return 0.0
    
    # 最も右側のHP位置から割合を計算
    rightmost_hp = max(hp_positions)
    percentage = (rightmost_hp / (width - 1)) * 100
    
    return min(percentage, 100.0)

# --- 実行 ---
if __name__ == '__main__':
    screenshot_file = 'pokemon_screenshot.png'  # ここに画像のパスを指定
    hp = get_hp_percentage(screenshot_file)
    
    print(f"残りのHP割合: {hp:.2f}%")