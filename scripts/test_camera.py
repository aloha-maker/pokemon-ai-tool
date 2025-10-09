
import cv2
import argparse

def test_camera_device(index):
    """指定されたインデックスのカメラデバイスをテストし、映像をウィンドウに表示する。"""
    print(f"カメラテストを開始します。インデックス: {index}")
    
    # CAP_DSHOW をつけて試す
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print(f"エラー: カメラ {index} を開けませんでした。")
        print("インデックスが間違っているか、他のアプリケーションがカメラを使用中の可能性があります。")
        return

    print("カメラを開きました。映像ウィンドウが表示されます。")
    print("ウィンドウを選択した状態で 'q' キーを押すと終了します。")

    window_name = f"Camera Test (Index: {index})"
    while True:
        ret, frame = cap.read()
        if not ret:
            print("エラー: カメラからフレームを読み取れませんでした。")
            break
        
        cv2.imshow(window_name, frame)
        
        # 1ms待機し、'q'キーが押されたらループを抜ける
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    print("テストを終了します。")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test a camera device with OpenCV.')
    parser.add_argument('--index', type=int, default=0, help='Index of the camera device to test.')
    args = parser.parse_args()
    
    test_camera_device(args.index)
