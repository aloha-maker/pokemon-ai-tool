import os
import glob
from PIL import Image

# --- 設定パラメータ ---
# Tesseractの命名規則に基づくベース名を設定します。
# 例: 'eng.fontname.exp0'
BASE_NAME = 'jpn.customfont.exp0' 
OUTPUT_DIR = './output_tesseract_files' # 出力ディレクトリ
INPUT_DIR = r'C:\Users\daiki\Videos\pokemon\train_data'             # 個別ファイルがあるディレクトリ

# --- メイン処理 ---
def merge_tesseract_files():
    # 入出力ディレクトリの作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # globを使用して連番のファイルを取得（ソートしてページ順を保証）
    # 対応する画像ファイル名には必ず連番を含むようにしてください (例: page_001.png, page_002.png)
    image_files = sorted(glob.glob(os.path.join(INPUT_DIR, '*.jpg')))
    if not image_files:
        print(f"エラー: {INPUT_DIR} 内に .png ファイルが見つかりません。")
        return

    # --- 1. マルチページTIFFの作成 ---
    tiff_output_path = os.path.join(OUTPUT_DIR, f'{BASE_NAME}.tif')
    tiff_images = [Image.open(f) for f in image_files]
    
    # 最初の画像をマスターとして、残りの画像をappend_imagesで結合
    tiff_images[0].save(
        tiff_output_path,
        save_all=True,
        append_images=tiff_images[1:],
        compression="tiff_deflate" # 可逆圧縮 (Zip/Deflate) を使用
    )
    print(f"✅ マルチページTIFFを作成しました: {tiff_output_path}")

    # --- 2. Boxファイルの統合とページ番号の追加 ---
    box_output_path = os.path.join(OUTPUT_DIR, f'{BASE_NAME}.box')
    
    with open(box_output_path, 'w', encoding='utf-8', newline='\n') as outfile:
        for page_num, img_file in enumerate(image_files):
            # 画像ファイル名から対応するBoxファイル名を推測（拡張子を.boxに変更）
            # 例: input_pages/page_001.png -> input_pages/page_001.box
            base_filename = os.path.splitext(os.path.basename(img_file))[0]
            box_file_path = os.path.join(INPUT_DIR, f'{base_filename}.box')

            if not os.path.exists(box_file_path):
                print(f"警告: Boxファイルが見つかりません: {box_file_path}")
                continue
            
            with open(box_file_path, 'r', encoding='utf-8', newline='\n') as infile:
                for line in infile:
                
                    parts = line.strip().split()
                    if not parts: 
                        continue
                    
                    if len(parts) < 5:
                        print(f"警告: 不正な行をスキップ: {line.strip()}")
                        continue

                    # 最初の5要素（文字と座標）のみを使用
                    char, x1, y1, x2, y2 = parts[0], parts[1], parts[2], parts[3], parts[4]
                    
                    # 厳密に6列形式で書き出し、新しいページ番号を強制的に適用
                    new_line = f"{char} {x1} {y1} {x2} {y2} {page_num}\n"
                    outfile.write(new_line)
    
    print(f"✅ 統合Boxファイルを作成しました: {box_output_path}")

if __name__ == '__main__':
    merge_tesseract_files()