import os
import subprocess
import glob

def train_tesseract_with_python(dataset_dir, prefix):
    """
    PythonからTesseract学習を実行
    """
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # トレーニングファイルのパス
    training_list = os.path.join(dataset_dir, f"{prefix}.training_files.txt")
    
    # コマンド構築
    cmd = [
        tesseract_path,
        training_list,
        "nobatch",
        "box.train"
    ]
    
    print("🎯 Tesseract学習を開始します...")
    print(f"コマンド: {' '.join(cmd)}")
    
    try:
        # カレントディレクトリをdatasetに変更して実行
        original_dir = os.getcwd()
        os.chdir(dataset_dir)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 学習が正常に完了しました！")
        else:
            print("❌ 学習中にエラーが発生しました:")
            print("標準出力:", result.stdout)
            print("標準エラー:", result.stderr)
            
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
    finally:
        os.chdir(original_dir)

def create_box_files(dataset_dir, prefix):
    """
    ボックスファイルを生成（学習の第一段階）
    """
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # PNGファイルのリストを取得
    png_files = glob.glob(os.path.join(dataset_dir, "*.png"))
    
    print("🎯 ボックスファイルを生成します...")
    
    for png_file in png_files:
        base_name = os.path.splitext(os.path.basename(png_file))[0]
        image_path = os.path.join(dataset_dir, base_name + ".png")
        
        cmd = [
            tesseract_path,
            image_path,
            os.path.join(dataset_dir, base_name),
            "-l", "jpn",
            "batch.nochop",
            "makebox"
        ]
        
        print(f"処理中: {base_name}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=dataset_dir)
            if result.returncode == 0:
                print(f"✅ {base_name}.box を生成")
            else:
                print(f"❌ {base_name} の処理に失敗")
                print("エラー:", result.stderr)
        except Exception as e:
            print(f"❌ エラー: {e}")

def main_training(dataset_dir, prefix):
    """
    学習プロセスを一括実行
    """
    print("🎯 Tesseract学習プロセスを開始します...")
    
    # 1. ボックスファイル生成
    print("\n1. ボックスファイル生成")
    create_box_files(dataset_dir, prefix)
    
    # 2. メイン学習
    print("\n2. メイン学習の実行")
    train_tesseract_with_python(dataset_dir, prefix)
    
    print("\n🎉 学習プロセスが完了しました！")

# 実行
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("使用法: python train_tesseract.py <dataset_dir> <file_prefix>")
        print("例: python train_tesseract.py dataset jpn.pkmn")
        sys.exit(1)
    
    dataset_dir = sys.argv[1]
    file_prefix = sys.argv[2]
    
    if not os.path.exists(dataset_dir):
        print(f"エラー: ディレクトリが見つかりません: {dataset_dir}")
        sys.exit(1)
    
    main_training(dataset_dir, file_prefix)