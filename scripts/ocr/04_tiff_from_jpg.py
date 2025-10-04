from PIL import Image
import os
import glob

def convert_jpg_to_tif(input_path, output_path=None):
    """
    JPG画像をTIFF形式に変換する関数
    
    Args:
        input_path (str): 入力JPGファイルのパス
        output_path (str, optional): 出力TIFFファイルのパス。指定しない場合は入力ファイル名を基に自動生成
    """
    try:
        # 入力ファイルの存在確認
        if not os.path.exists(input_path):
            print(f"エラー: ファイル '{input_path}' が見つかりません")
            return False
        
        # 出力ファイル名の生成
        if output_path is None:
            base_name = os.path.splitext(input_path)[0]
            output_path = base_name + '.tif'
        
        # 画像の読み込みと変換
        with Image.open(input_path) as img:
            # TIFF形式で保存
            img.save(output_path, 'TIFF')
        
        print(f"変換成功: {input_path} → {output_path}")
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def convert_directory(input_dir, output_dir=None):
    """
    ディレクトリ内のすべてのJPGファイルをTIFFに変換する関数
    
    Args:
        input_dir (str): 入力ディレクトリのパス
        output_dir (str, optional): 出力ディレクトリのパス
    """
    if output_dir is None:
        output_dir = input_dir
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    # JPGファイルを検索
    jpg_files = glob.glob(os.path.join(input_dir, "*.jpg"))
    
    if not jpg_files:
        print(f"{input_dir} にJPGファイルが見つかりません")
        return
    
    print(f"{len(jpg_files)} 個のJPGファイルを変換します...")
    
    success_count = 0
    for jpg_file in jpg_files:
        # 出力ファイル名を生成
        base_name = os.path.splitext(os.path.basename(jpg_file))[0]
        output_file = os.path.join(output_dir, base_name + '.tif')
        
        # 変換実行
        if convert_jpg_to_tif(jpg_file, output_file):
            success_count += 1
    
    print(f"変換完了: {success_count}/{len(jpg_files)} ファイル")

# 使用例
if __name__ == "__main__":
    # 単一ファイルの変換
    # convert_jpg_to_tif(r"C:\workspace\tesstrain\data\jpn_pokemon-ground-truth\3cb86be6_008400.jpg", r"C:\workspace\tesstrain\data\jpn_pokemon-ground-truth\3cb86be6_008400.tif")
    
    # ディレクトリ内の全ファイルを変換
    convert_directory(r"C:\workspace\tesstrain\data\jpn_pokemon-ground-truth", r"C:\workspace\tesstrain\data\jpn_pokemon-ground-truth")