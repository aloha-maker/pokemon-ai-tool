import cv2
import argparse
import json

# コマンドライン引数の設定
parser = argparse.ArgumentParser(description='Select Regions of Interest (ROI) from an image and save to JSON.')
parser.add_argument('-i', '--image', required=True, help='Path to the input image.')
args = parser.parse_args()

# 画像を読み込む
img = cv2.imread(args.image)
if img is None:
    print(f"Error: Could not read image from {args.image}")
    exit()

print("--- ROI Selector ---")
print("1. マウスをドラッグして範囲を選択してください。")
print("2. Enterキーを押して選択を確定します。")
print("3. ウィンドウをxボタンで閉じるか、何も選択せずにEnterを押すと終了し、ファイルに保存されます。")
print("--------------------")

rois = {}
roi_count = 1

while True:
    # ROIを選択
    roi = cv2.selectROI("Select ROI", img, fromCenter=False, showCrosshair=True)
    x, y, w, h = roi

    # ユーザーが選択を終えたか確認 (何も選択せずにEnterか、ウィンドウを閉じる)
    if w == 0 and h == 0:
        cv2.destroyAllWindows()
        break

    # 選択範囲を一時的に表示
    img_copy = img.copy()
    cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imshow("Current Selection", img_copy)
    
    # ROIの名前を入力
    roi_name = input(f"ROI_{roi_count} の名前を入力してください (例: my_pokemon_name): ")
    if not roi_name:
        roi_name = f"roi_{roi_count}"

    # 辞書に保存
    rois[roi_name] = (x, y, w, h)
    print(f"'{roi_name}': {(x, y, w, h)} を追加しました。\n")
    
    roi_count += 1
    cv2.destroyWindow("Current Selection")

# ループ終了後、JSONファイルに保存
if rois:
    with open('instance/roi_config.json', 'w', encoding='utf-8') as f:
        json.dump(rois, f, indent=4, ensure_ascii=False)
    print("\nROI設定を 'instance/roi_config.json' に保存しました。")
else:
    print("\nROIは選択されませんでした。ファイルは保存されません。")

print("スクリプトを終了します。")
