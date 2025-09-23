import os
import glob
import cv2

def prepare_training_with_png(dataset_dir, prefix):
    """
    PNGファイルで学習準備を完了する
    """
    print("🎯 PNGファイルを使用した学習準備を開始します...")
    
    # 1. ファイルリストの作成
    png_files = glob.glob(os.path.join(dataset_dir, "*.png"))
    txt_files = glob.glob(os.path.join(dataset_dir, "*.gt.txt"))
    
    print(f"📊 検出されたファイル:")
    print(f"  PNGファイル: {len(png_files)}個")
    print(f"  テキストファイル: {len(txt_files)}個")
    
    # 2. トレーニングファイルリストの作成
    list_path = os.path.join(dataset_dir, f"{prefix}.training_files.txt")
    
    with open(list_path, 'w', encoding='utf-8') as f:
        for png_file in png_files:
            filename = os.path.basename(png_file)
            f.write(filename + '\n')
    
    print(f"✅ トレーニングファイルリスト: {list_path}")
    
    # 3. 学習用コマンドの表示
    print("\n🎯 以下のコマンドで学習を開始できます:")
    print(f"cd {dataset_dir}")
    print(f"tesseract {prefix}.training_files.txt nobatch box.train")
    
    # 4. 最初のファイルでテスト実行する場合
    if png_files:
        first_file_base = os.path.basename(png_files[0]).replace('.png', '')
        print(f"\n🔧 テスト実行（最初のファイル）:")
        print(f"tesseract {first_file_base}.png {first_file_base} -l jpn batch.nochop makebox")

# 実行
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("使用法: python prepare_png_training.py <dataset_dir> <file_prefix>")
        print("例: python prepare_png_training.py dataset jpn.pkmn")
        sys.exit(1)
    
    dataset_dir = sys.argv[1]
    file_prefix = sys.argv[2]
    
    if not os.path.exists(dataset_dir):
        print(f"エラー: ディレクトリが見つかりません: {dataset_dir}")
        sys.exit(1)
    
    prepare_training_with_png(dataset_dir, file_prefix)