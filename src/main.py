import cv2
from core.capture import ScreenCapturer
from core.ocr import GameStateParser
from ai.predictor import ActionAIModel
import time
import pprint

TARGET_WINDOW_TITLE = "ChatGPT Image 2025年9月13日 11_52_02.png" 

def main():
    capturer = ScreenCapturer(TARGET_WINDOW_TITLE)
    parser = GameStateParser()
    model = ActionAIModel() # AIモデルをインスタンス化

    print(f"'{TARGET_WINDOW_TITLE}' のキャプチャと解析を開始します。")
    print("プレビューウィンドウで 'q' キーを押すと終了します。")

    last_recommendation_time = time.time()

    while True:
        frame = capturer.capture_frame()

        if frame is not None:
            # 2秒ごとに解析と推論を実行 (負荷軽減のため)
            if time.time() - last_recommendation_time > 2:
                # 1. 盤面情報を抽出
                current_state = parser.parse_frame(frame)
                
                # 2. AIモデルで行動を予測
                recommendation = model.predict_action(current_state)

                # 3. 結果をコンソールに表示
                print("\n--- [盤面情報] ---")
                pprint.pprint(current_state)
                print("--- [AIの推奨] ---")
                pprint.pprint(recommendation)
                print("--------------------")
                
                last_recommendation_time = time.time()

            cv2.imshow("Game Capture Preview", frame)
        else:
            time.sleep(1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    print("処理を終了しました。")

if __name__ == "__main__":
    main()
