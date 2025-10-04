import os
import cv2
import pytesseract
from PIL import Image
import re

class OCRTextGenerator:
    def __init__(self):
        """
        OCRテキスト生成クラス（ディレクトリ直書き版）
        """
        # ディレクトリパスを直書き
        self.image_dir = r'C:\Users\daiki\Videos\pokemon\input_img'
        self.output_text_dir = r'C:\Users\daiki\Videos\pokemon\output_text'
        
        # Tesseractのパス設定
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # 出力ディレクトリを作成
        os.makedirs(self.output_text_dir, exist_ok=True)
        
        # ポケモン対戦でよく使われる単語を辞書に追加（精度向上のため）
        self.custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789- '
    
    def preprocess_image(self, image_path):
        """
        画像の前処理を行う
        """
        # 画像を読み込み
        image = cv2.imread(image_path)
        if image is None:
            print(f"警告: {image_path} を読み込めませんでした")
            return None
        
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # ノイズ除去
        denoised = cv2.medianBlur(gray, 3)
        
        # 二値化（大津の方法）
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def extract_text_from_image(self, image_path):
        """
        画像からテキストを抽出する
        """
        # 画像前処理
        processed_image = self.preprocess_image(image_path)
        if processed_image is None:
            return ""
        
        try:
            # OCRでテキスト抽出
            text = pytesseract.image_to_string(
                processed_image, 
                config=self.custom_config,
                lang='eng'
            )
            
            # テキストのクリーニング
            cleaned_text = self.clean_text(text)
            
            return cleaned_text
            
        except Exception as e:
            print(f"エラー: {image_path} の処理中に問題が発生: {e}")
            return ""
    
    def clean_text(self, text):
        """
        抽出したテキストをクリーニングする
        """
        # 改行と余分な空白を除去
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 特殊文字を除去（英数字とハイフンのみ許可）
        text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
        
        # 連続するハイフンを単一のハイフンに
        text = re.sub(r'-+', '-', text)
        
        return text.strip()
    
    def generate_text_files(self):
        """
        すべての画像に対してテキストファイルを生成する
        """
        # 対応する画像形式
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        
        # 画像ファイルのリストを取得
        image_files = [
            f for f in os.listdir(self.image_dir)
            if os.path.splitext(f)[1].lower() in valid_extensions
        ]
        
        if not image_files:
            print("画像ファイルが見つかりません")
            print(f"確認先: {self.image_dir}")
            return
        
        print(f"{len(image_files)}個の画像ファイルを処理します...")
        print(f"入力ディレクトリ: {self.image_dir}")
        print(f"出力ディレクトリ: {self.output_text_dir}")
        print("-" * 50)
        
        success_count = 0
        
        for image_file in image_files:
            image_path = os.path.join(self.image_dir, image_file)
            
            # テキスト抽出
            extracted_text = self.extract_text_from_image(image_path)
            
            if extracted_text:
                # テキストファイル名を生成（拡張子を.txtに変更）
                base_name = os.path.splitext(image_file)[0]
                text_file_name = f"{base_name}.gt.txt"
                text_file_path = os.path.join(self.output_text_dir, text_file_name)
                
                # テキストファイルを保存
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                
                print(f"✓ {text_file_name} -> '{extracted_text}'")
                success_count += 1
            else:
                print(f"✗ {image_file} (テキストを抽出できませんでした)")
        
        print("-" * 50)
        print(f"処理完了: {success_count}/{len(image_files)}個のテキストファイルを生成しました")
        
        # 結果のサマリーを表示
        if success_count == 0:
            print("⚠ テキストを抽出できた画像がありません。以下の点を確認してください:")
            print("  - 画像ファイルが正しいディレクトリにあるか")
            print("  - 画像にテキストが含まれているか")
            print("  - Tesseractが正しくインストールされているか")

def main():
    """
    メイン実行関数
    """
    print("OCRテキスト自動生成スクリプトを開始します...")
    print("設定:")
    print(f"  画像ディレクトリ: C:\\Users\\daiki\\Videos\\pokemon\\input_img")
    print(f"  テキスト出力先: C:\\Users\\daiki\\Videos\\pokemon\\output_text")
    print(f"  Tesseractパス: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
    print()
    
    # OCRテキスト生成を実行
    generator = OCRTextGenerator()
    generator.generate_text_files()
    
    print()
    print("次のステップ:")
    print("1. 生成されたテキストファイルを手動で確認・修正してください")
    print("2. 修正後、Tesstrain用のデータセットとして使用できます")

if __name__ == "__main__":
    main()