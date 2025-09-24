import os
import subprocess
import glob

def train_tesseract_with_python(dataset_dir, prefix):
    """
    PythonからTesseract学習を実行（修正版）
    """
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # トレーニングファイルのパス
    training_list = f"{prefix}.training_files.txt"
    training_list_path = os.path.join(dataset_dir, training_list)
    
    # ファイルの存在確認
    if not os.path.exists(training_list_path):
        print(f"❌ トレーニングファイルが見つかりません: {training_list_path}")
        print("📋 以下のファイルが存在します:")
        for file in os.listdir(dataset_dir):
            print(f"  - {file}")
        return
    
    print(f"✅ トレーニングファイルを発見: {training_list}")
    
    # 作業ディレクトリを変更してからコマンド実行
    original_dir = os.getcwd()
    
    try:
        os.chdir(dataset_dir)
        
        # 相対パスでコマンド構築（作業ディレクトリ内で実行）
        cmd = [
            tesseract_path,
            training_list,  # ファイル名のみ（カレントディレクトリ内）
            prefix,         # 出力ベース名のみ
            "-l", "jpn",    # ベース言語を指定
            "nobatch",
            "box.train"
        ]
        
        print("🎯 Tesseract学習を開始します...")
        print(f"コマンド: {' '.join(cmd)}")
        print(f"作業ディレクトリ: {os.getcwd()}")
        
        # トレーニングファイルの内容を確認
        print(f"📋 トレーニングファイルの内容:")
        with open(training_list, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:5]):  # 最初の5行を表示
                print(f"  {i+1}: {line.strip()}")
            if len(lines) > 5:
                print(f"  ... 他 {len(lines)-5} 行")
        
        # 実行（エンコーディング問題を解決）
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,
            encoding='utf-8',
            errors='replace'  # エンコーディングエラーを置換文字で処理
        )
        
        if result.returncode == 0:
            print("✅ 学習が正常に完了しました！")
            if result.stdout:
                print("📄 出力:", result.stdout)
        else:
            print("❌ 学習中にエラーが発生しました:")
            print(f"Return code: {result.returncode}")
            if result.stdout:
                print("標準出力:", result.stdout)
            if result.stderr:
                print("標準エラー:", result.stderr)
                
    except subprocess.TimeoutExpired:
        print("❌ 学習がタイムアウトしました（5分超過）")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
    finally:
        os.chdir(original_dir)

def train_tesseract_alternative(dataset_dir, prefix):
    """
    代替の学習方法（個別ファイル処理）
    """
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # 作業ディレクトリを変更
    original_dir = os.getcwd()
    os.chdir(dataset_dir)
    
    try:
        # PNGファイルとボックスファイルのペアを取得
        png_files = glob.glob(f"{prefix}.*.png")
        
        print("🎯 代替学習方法を実行します...")
        print(f"📊 処理対象ファイル数: {len(png_files)}")
        
        successful_count = 0
        
        for i, png_file in enumerate(png_files):
            base_name = os.path.splitext(png_file)[0]
            box_file = base_name + ".box"
            
            # ボックスファイルの存在確認
            if not os.path.exists(box_file):
                print(f"⚠️ ボックスファイルが見つかりません: {box_file}")
                continue
            
            print(f"🔧 学習中 ({i+1}/{len(png_files)}): {base_name}")
            
            # 個別ファイルでの学習コマンド
            cmd = [
                tesseract_path,
                png_file,        # PNGファイル名
                base_name,       # 出力ベース名
                "-l", "jpn",
                "nobatch",
                "box.train"
            ]
            
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    encoding='utf-8',
                    errors='replace'  # エンコーディングエラーを置換文字で処理
                )
                
                if result.returncode == 0:
                    print(f"  ✅ {base_name} 学習完了")
                    successful_count += 1
                else:
                    print(f"  ❌ {base_name} エラー (code: {result.returncode})")
                    if result.stderr:
                        # エラーメッセージの最初の行のみ表示（長すぎる場合に備えて）
                        error_lines = result.stderr.strip().split('\n')
                        print(f"     {error_lines[0]}")
                        
            except subprocess.TimeoutExpired:
                print(f"  ❌ {base_name} タイムアウト")
            except Exception as e:
                print(f"  ❌ {base_name} 実行エラー: {e}")
        
        print(f"📊 代替学習完了: {successful_count}/{len(png_files)} 成功")
        
    finally:
        os.chdir(original_dir)

def create_box_files(dataset_dir, prefix):
    """
    ボックスファイルを生成（学習の第一段階）- 修正版
    """
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    # 作業ディレクトリを変更
    original_dir = os.getcwd()
    os.chdir(dataset_dir)
    
    try:
        # PNGファイルのリストを取得
        png_files = glob.glob(f"{prefix}.*.png")
        
        print("🎯 ボックスファイルを生成します...")
        print(f"📊 処理対象ファイル数: {len(png_files)}")
        
        successful_count = 0
        
        for i, png_file in enumerate(png_files):
            base_name = os.path.splitext(png_file)[0]
            
            print(f"🔧 処理中 ({i+1}/{len(png_files)}): {png_file}")
            
            cmd = [
                tesseract_path,
                png_file,        # ファイル名のみ
                base_name,       # 出力ベース名
                "-l", "jpn",
                "batch.nochop",
                "makebox"
            ]
            
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    encoding='utf-8',
                    errors='replace'  # エンコーディングエラーを置換文字で処理
                )
                
                if result.returncode == 0:
                    # ボックスファイルが生成されたか確認
                    box_file = base_name + ".box"
                    if os.path.exists(box_file):
                        print(f"  ✅ {base_name}.box を生成")
                        successful_count += 1
                    else:
                        print(f"  ⚠️ ボックスファイルが生成されませんでした")
                else:
                    print(f"  ❌ エラー (code: {result.returncode})")
                    if result.stderr:
                        # エラーメッセージの最初の行のみ表示
                        error_lines = result.stderr.strip().split('\n')
                        print(f"     {error_lines[0]}")
                        
            except subprocess.TimeoutExpired:
                print(f"  ❌ {png_file} タイムアウト")
            except Exception as e:
                print(f"  ❌ 実行エラー: {e}")
        
        print(f"📊 ボックスファイル生成完了: {successful_count}/{len(png_files)} 成功")
        
    finally:
        os.chdir(original_dir)

def check_training_files(dataset_dir, prefix):
    """
    トレーニングファイルの内容を検証
    """
    training_list_path = os.path.join(dataset_dir, f"{prefix}.training_files.txt")
    
    if not os.path.exists(training_list_path):
        print(f"❌ トレーニングファイルが見つかりません: {training_list_path}")
        return False
    
    print(f"📋 トレーニングファイルの検証: {training_list_path}")
    
    with open(training_list_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    print(f"📊 登録ファイル数: {len(lines)}")
    
    # ファイルの存在確認
    missing_files = []
    for i, filename in enumerate(lines[:10]):  # 最初の10ファイルをチェック
        file_path = os.path.join(dataset_dir, filename)
        if os.path.exists(file_path):
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename} - ファイルが見つかりません")
            missing_files.append(filename)
    
    if missing_files:
        print(f"⚠️ {len(missing_files)}個のファイルが見つかりません")
        return False
    
    return True

def create_correct_training_list(dataset_dir, prefix):
    """
    正しいトレーニングファイルリストを作成
    """
    # 指定されたプレフィックスのPNGファイルをリストアップ
    png_files = [f for f in os.listdir(dataset_dir) if f.startswith(prefix) and f.endswith('.png')]
    png_files.sort()  # ソート
    
    training_list_path = os.path.join(dataset_dir, f"{prefix}.training_files.txt")
    
    with open(training_list_path, 'w', encoding='utf-8') as f:
        for filename in png_files:
            f.write(filename + '\n')
    
    print(f"✅ トレーニングファイルリストを再生成: {training_list_path}")
    print(f"📊 登録ファイル数: {len(png_files)}")

def check_tesseract_version():
    """
    Tesseractのバージョンを確認
    """
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    try:
        result = subprocess.run(
            [tesseract_path, "--version"], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='replace'  # エンコーディングエラーを置換文字で処理
        )
        if result.stdout:
            version_line = result.stdout.split('\n')[0]
            print(f"📋 Tesseract バージョン: {version_line}")
            
            # バージョン4以降かチェック
            if "tesseract 4" in version_line.lower() or "tesseract 5" in version_line.lower():
                print("ℹ️ Tesseract 4.x/5.x が検出されました。LSTM学習も利用可能です。")
            else:
                print("ℹ️ 従来のTesseract学習方式を使用します。")
    except Exception as e:
        print(f"⚠️ Tesseractバージョン確認エラー: {e}")

def main_training(dataset_dir, prefix):
    """
    学習プロセスを一括実行（修正版）
    """
    print("🎯 Tesseract学習プロセスを開始します...")
    print(f"📁 データセットディレクトリ: {dataset_dir}")
    print(f"🏷️ プレフィックス: {prefix}")
    
    # バージョン確認
    check_tesseract_version()
    
    # 0. トレーニングファイルの確認と再生成
    print("\n0. トレーニングファイルの確認")
    if not check_training_files(dataset_dir, prefix):
        print("📝 トレーニングファイルを再生成します...")
        create_correct_training_list(dataset_dir, prefix)
    
    # 1. ボックスファイル生成
    print("\n1. ボックスファイル生成")
    create_box_files(dataset_dir, prefix)
    
    # 2. メイン学習（従来方式）
    print("\n2. メイン学習の実行（従来方式）")
    train_tesseract_with_python(dataset_dir, prefix)
    
    # 3. 代替学習方法も試行
    print("\n3. 代替学習方法の実行")
    train_tesseract_alternative(dataset_dir, prefix)
    
    print("\n🎉 学習プロセスが完了しました！")
    
    # 生成されたファイルの確認
    print("\n📋 生成されたファイル:")
    for file in os.listdir(dataset_dir):
        if file.startswith(prefix) and (file.endswith('.traineddata') or file.endswith('.tr')):
            print(f"  ✅ {file}")

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