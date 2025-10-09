from PIL import Image
import os
import glob

def convert_png_to_tif(input_path, output_path=None):
    """
    PNG画像をTIFF形式に変換する関数
    
    Args:
        input_path (str): 入力PNGファイルのパス
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
    ディレクトリ内のすべてのPNGファイルをTIFFに変換する関数
    
    Args:
        input_dir (str): 入力ディレクトリのパス
        output_dir (str, optional): 出力ディレクトリのパス
    """
    if output_dir is None:
        output_dir = input_dir
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    # PNGファイルを検索
    png_files = glob.glob(os.path.join(input_dir, "*.png"))
    
    if not png_files:
        print(f"{input_dir} にPNGファイルが見つかりません")
        return
    
    print(f"{len(png_files)} 個のPNGファイルを変換します...")
    
    success_count = 0
    for png_file in png_files:
        # 出力ファイル名を生成
        base_name = os.path.splitext(os.path.basename(png_file))[0]
        output_file = os.path.join(output_dir, base_name + '.tif')
        
        # 変換実行
        if convert_png_to_tif(png_file, output_file):
            success_count += 1
    
    print(f"変換完了: {success_count}/{len(png_file)} ファイル")

# 使用例
if __name__ == "__main__":
    # 単一ファイルの変換
    # convert_jpg_to_tif(r"C:\workspace\tesstrain\data\jpn_pokemon-ground-truth\3cb86be6_008400.jpg", r"C:\workspace\tesstrain\data\jpn_pokemon-ground-truth\3cb86be6_008400.tif")
    
    # ディレクトリ内の全ファイルを変換
    convert_directory(r"C:\pokemon-ai-tool\.traindata\text2img", r"C:\pokemon-ai-tool\.traindata\text2img")