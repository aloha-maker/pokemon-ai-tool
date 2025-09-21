
import cv2
import sys
import os
import numpy as np

def main(video_path, template_path):
    """
    動画全体をスキャンし、テンプレート画像との一致度が最も高い上位5フレームを検出・保存する。
    """
    output_dir = "verification_results/debug"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- 動画とテンプレートの読み込み ---
    if not os.path.exists(video_path):
        print(f"エラー: 動画ファイルが見つかりません: {video_path}")
        return
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"エラー: 動画ファイルを開けません: {video_path}")
        return

    if not os.path.exists(template_path):
        print(f"エラー: テンプレートファイルが見つかりません: {template_path}")
        return
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        print(f"エラー: テンプレートファイルの読み込みに失敗しました: {template_path}")
        return
    h, w = template.shape

    print(f"Starting debug run. Template: {template_path}")

    top_matches = []  # (score, frame_number, location, frame_image)
    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # --- 全フレームをスキャン ---
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        res = cv2.matchTemplate(frame_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        # 上位5件を保持するロジック
        if len(top_matches) < 5:
            top_matches.append((max_val, frame_count, max_loc, frame.copy()))
            top_matches.sort(key=lambda x: x[0], reverse=True)
        elif max_val > top_matches[-1][0]:
            top_matches.pop()
            top_matches.append((max_val, frame_count, max_loc, frame.copy()))
            top_matches.sort(key=lambda x: x[0], reverse=True)
        
        if frame_count % 200 == 0:
            print(f"  ... processed {frame_count} / {total_frames} frames.")
        
        frame_count += 1

    cap.release()

    # --- 結果の出力 ---
    print("\n--- Top 5 Template Matches ---")
    for i, (score, f_num, loc, f_img) in enumerate(top_matches):
        print(f"Rank {i+1}: Frame {f_num}, Score: {score:.4f}")
        
        top_left = loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        cv2.rectangle(f_img, top_left, bottom_right, (0, 0, 255), 2)
        cv2.putText(f_img, f"Score: {score:.2f}", (top_left[0], top_left[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        
        output_path = os.path.join(output_dir, f"debug_match_{i+1}_frame_{f_num}.png")
        cv2.imwrite(output_path, f_img)
        print(f"  -> Saved result to {output_path}")

    print("\nDebug verification complete.")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    else:
        print("使用法: python debug_template_matching.py <video_path> <template_path>")
