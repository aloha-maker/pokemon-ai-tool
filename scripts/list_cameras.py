import cv2

def list_available_cameras():
    """
    利用可能なカメラデバイスをスキャンし、インデックスと情報を表示する。
    0から9までのインデックスをすべて試し、それぞれが開けるかどうかを報告する。
    """
    print("0から9までのカメラデバイスインデックスをスキャンしています...")
    
    found_any = False
    for index in range(10):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            backend_name = cap.getBackendName()
            print(f"  (OK)   インデックス: {index} - 開くことに成功しました (バックエンド: {backend_name})")
            cap.release()
            found_any = True
        else:
            print(f"  (Fail) インデックス: {index} - 開けませんでした")

    print("\n--- スキャン完了 ---")
    if not found_any:
        print("利用可能なカメラが見つかりませんでした。")
    else:
        print("OBS Virtual Cameraに対応すると思われるインデックスをUIに入力してください。")
        print("（OBSで仮想カメラを開始した状態で、このスクリプトを実行してください）")


if __name__ == "__main__":
    list_available_cameras()