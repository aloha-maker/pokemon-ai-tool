import os
import cv2
import pytesseract
from PIL import Image
import re
import shutil


class OCRTextGenerator:
    def __init__(self):
        """
        OCRテキスト生成クラス（ディレクトリ直書き版）
        """
        # ディレクトリパスを直書き
        self.image_dir = r"C:\pokemon-ai-tool\.traindata\text2img"
        # self.output_dir = r'C:\workspace\tesstrain\data\jpn_pokemon-ground-truth'

        # Tesseractのパス設定
        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

        # tessdata_custom への絶対パスを構築
        script_path = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
        tessdata_dir = os.path.join(project_root, "tessdata_custom")
        self.custom_config = f"--tessdata-dir {tessdata_dir} --oem 3 --psm 7"

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
        画像からテキストと確信度統計（最大・中央値・平均）を抽出する
        """
        processed_image = self.preprocess_image(image_path)
        if processed_image is None:
            return "", {"max": 0, "median": 0, "avg": 0}

        try:
            data = pytesseract.image_to_data(
                processed_image,
                config=self.custom_config,
                lang='jpn+jpn_pokemon',
                output_type=pytesseract.Output.DICT
            )

            # テキスト結合
            text = " ".join([t for t in data['text'] if t.strip() != ""])
            cleaned_text = self.clean_text(text)

            # 確信度の統計計算
            conf_values = [float(c) for c in data['conf'] if c != '-1']
            if conf_values:
                max_conf = max(conf_values)
                median_conf = sorted(conf_values)[len(conf_values) // 2]
                avg_conf = sum(conf_values) / len(conf_values)
            else:
                max_conf = median_conf = avg_conf = 0.0

            conf_stats = {
                "max": max_conf,
                "median": median_conf,
                "avg": avg_conf
            }

            return cleaned_text, conf_stats

        except Exception as e:
            print(f"エラー: {image_path} の処理中に問題が発生: {e}")
            return "", {"max": 0, "median": 0, "avg": 0}


    def clean_text(self, text):
        """
        抽出したテキストをクリーニングする
        """
        # 空白文字（スペース、改行など）をすべて削除
        cleaned_text = re.sub(r"\s+", "", text)

        # 連続するハイフンを単一のハイフンに
        cleaned_text = re.sub(r"-+", "-", cleaned_text)

        return cleaned_text
    def generate_text_files(self):
        """
        すべての画像に対してテキストファイルを生成する
        （最大確信度90未満の画像は削除）
        """
        valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

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
        print(f"出力ディレクトリ: {self.image_dir}")
        print("-" * 50)

        success_count = 0
        deleted_count = 0

        for image_file in image_files:
            image_path = os.path.join(self.image_dir, image_file)

            # テキストと確信度統計を取得
            extracted_text, conf_stats = self.extract_text_from_image(image_path)
            max_conf = conf_stats["max"]

            # 最大確信度が90未満なら削除
            if max_conf < 90:
                try:
                    os.remove(image_path)
                    print(f"✗ {image_file} (最大確信度 {max_conf:.1f} < 90 → 削除)")
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠ {image_file} の削除に失敗しました: {e}")
                continue

            # テキスト出力処理
            if extracted_text:
                base_name = os.path.splitext(image_file)[0]
                text_file_name = f"{base_name}.gt.txt"
                text_file_path = os.path.join(self.image_dir, text_file_name)

                max_conf_int = int(conf_stats["max"])
                median_conf_int = int(conf_stats["median"])
                avg_conf_int = int(conf_stats["avg"])

                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(
                        f"{extracted_text}確信度：最大{max_conf_int}／中央値{median_conf_int}／平均{avg_conf_int}"
                    )

                print(f"✓ {text_file_name} -> '{extracted_text}' (確信度: 最大{max_conf_int}／中央値{median_conf_int}／平均{avg_conf_int})")
                success_count += 1
            else:
                print(f"✗ {image_file} (テキストを抽出できませんでした)")

        print("-" * 50)
        print(f"処理完了: {success_count}/{len(image_files)} 個のテキストファイルを生成しました")
        print(f"削除された低確信度画像: {deleted_count} 個")


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
