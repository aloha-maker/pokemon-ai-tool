# precise_box_generator.py
import os
import cv2
import pytesseract
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import shutil

class PreciseBoxFileGenerator:
    def __init__(self):
        """
        精密Boxファイル生成クラス
        """
        # ディレクトリパス
        self.input_img_dir = r'C:\Users\daiki\Videos\pokemon\input_img'
        self.output_text_dir = r'C:\Users\daiki\Videos\pokemon\output_text'
        self.train_data_dir = r'C:\Users\daiki\Videos\pokemon\train_data'
        
        # Tesseractのパス設定
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # 出力ディレクトリを作成
        os.makedirs(self.train_data_dir, exist_ok=True)
    
    def get_image_text_pairs(self):
        """
        画像とテキストのペアを取得する
        """
        image_files = {}
        text_files = {}
        
        # 画像ファイルを取得
        for file in os.listdir(self.input_img_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                base_name = os.path.splitext(file)[0]
                image_files[base_name] = file
        
        # テキストファイルを取得
        for file in os.listdir(self.output_text_dir):
            if file.endswith('.gt.txt'):
                base_name = file.replace('.gt.txt', '')
                text_files[base_name] = file
        
        # ペアを作成（両方存在するもののみ）
        pairs = []
        for base_name in image_files:
            if base_name in text_files:
                pairs.append({
                    'base_name': base_name,
                    'image_file': image_files[base_name],
                    'text_file': text_files[base_name]
                })
        
        return pairs
    
    def read_ground_truth_text(self, text_file_path):
        """
        正解テキストファイルを読み込む
        """
        try:
            with open(text_file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"エラー: テキストファイル {text_file_path} の読み込みに失敗: {e}")
            return ""

    def detect_character_positions(self, image_path, text):
        """
        文字の位置を検出する（指定された固定値と6文字固定で計算）
        """
        try:
            # 画像を読み込み (サイズ取得用)
            image = cv2.imread(image_path)
            if image is None:
                print(f"エラー: 画像 {image_path} を読み込めませんでした")
                return None
            
            height, width = image.shape[:2]

            # --- 指定された固定要件 ---
            FIXED_CHARS = 6
            CHAR_WIDTH = 35         # W35
            CHAR_HEIGHT = 38        # H38
            START_X = 22            # Xの1文字目の開始22
            CHAR_SPACING = 33       # 次の開始までの間隔33
            TOP_Y = 10              # Y10

            # テキストを6文字に整形 (6文字未満の場合ブランクで埋める)
            if len(text) < FIXED_CHARS:
                processed_text = text.ljust(FIXED_CHARS, ' ')
            else:
                # 6文字を超える場合は切り捨て
                processed_text = text[:FIXED_CHARS]
            
            # 文字の位置を計算
            positions = []
            
            for i, char in enumerate(processed_text):
                # X座標
                left = START_X + (i * CHAR_SPACING)
                right = left + CHAR_WIDTH
                
                # Y座標
                top = TOP_Y
                bottom = top + CHAR_HEIGHT
                
                positions.append({
                    'char': char,
                    'left': left,
                    'top': top,
                    'right': right,
                    'bottom': bottom
                })
            
            return positions, width, height
            
        except Exception as e:
            print(f"エラー: 文字位置検出に失敗 {image_path}: {e}")
            return None
    
    # def detect_character_positions(self, image_path, text):
    #     """
    #     文字の位置を検出する（簡易的な実装）
    #     """
    #     try:
    #         # 画像を読み込み
    #         image = cv2.imread(image_path)
    #         if image is None:
    #             print(f"エラー: 画像 {image_path} を読み込めませんでした")
    #             return None
            
    #         height, width = image.shape[:2]
            
    #         # 文字の幅を計算（均等分割ではなく、文字数に基づく）
    #         char_width = width // len(text)
    #         char_height = 42  # 固定高さ（例に基づく）
            
    #         # 文字の位置を計算（例に基づくパターン）
    #         positions = []
    #         start_x = 22  # 例の開始X座標に基づく
            
    #         for i, char in enumerate(text):
    #             left = start_x + (i * 33)  # 例では約33ピクセル間隔
    #             right = left + 33  # 文字幅約33ピクセル
    #             top = 12  # 例の上端座標
    #             bottom = top + char_height  # 下端座標
                
    #             positions.append({
    #                 'char': char,
    #                 'left': left,
    #                 'top': top,
    #                 'right': right,
    #                 'bottom': bottom
    #             })
            
    #         return positions, width, height
            
    #     except Exception as e:
    #         print(f"エラー: 文字位置検出に失敗 {image_path}: {e}")
    #         return None
    
    def convert_coordinates_for_jtessboxeditor(self, left, bottom, right, top, image_height):
        """
        Tesseract座標系からjTessBoxEditor座標系に変換
        """
        jtess_top = image_height - bottom
        jtess_bottom = image_height - top
        
        return left, jtess_bottom, right, jtess_top
    
    def create_precise_box_file(self, image_path, text, output_box_path):
        """
        精密なboxファイルを作成する
        """
        try:
            # 文字位置を検出
            result = self.detect_character_positions(image_path, text)
            if result is None:
                return False
            
            positions, width, height = result
            
            box_lines = []
            
            for pos in positions:
                # jTessBoxEditor用の座標に変換
                jtess_left, jtess_bottom, jtess_right, jtess_top = self.convert_coordinates_for_jtessboxeditor(
                    pos['left'], pos['bottom'], pos['right'], pos['top'], height
                )
                
                # スペース文字の処理
                char_display = ' ' if pos['char'] == ' ' else pos['char']
                
                box_line = f"{char_display} {jtess_left} {jtess_bottom} {jtess_right} {jtess_top} 0"
                box_lines.append(box_line)
            
            # boxファイルを保存
            with open(output_box_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(box_lines))
            
            print(f"✓ Boxファイル生成: {os.path.basename(output_box_path)}")
            print(f"  文字数: {len(text)}, 画像サイズ: {width}x{height}")
            
            # 座標情報を表示
            print("  座標詳細:")
            for i, pos in enumerate(positions):
                print(f"    {pos['char']}: ({pos['left']}, {pos['top']}) - ({pos['right']}, {pos['bottom']})")
            
            return True
            
        except Exception as e:
            print(f"エラー: {image_path} のboxファイル作成に失敗: {e}")
            return False
    
    def create_adaptive_box_file(self, image_path, text, output_box_path):
        """
        画像解析に基づく適応的boxファイル作成
        """
        try:
            # 画像を読み込み
            image = cv2.imread(image_path)
            if image is None:
                return False
            
            height, width = image.shape[:2]
            
            # 画像を前処理
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 輪郭検出
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 文字領域と思われる輪郭をフィルタリング
            char_contours = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # 文字らしいサイズの輪郭を選択
                if 10 < w < 100 and 20 < h < 80:
                    char_contours.append((x, y, w, h))
            
            # 輪郭をX座標でソート
            char_contours.sort(key=lambda c: c[0])
            
            box_lines = []
            
            if len(char_contours) >= len(text):
                # 検出した輪郭を使用
                for i, (x, y, w, h) in enumerate(char_contours[:len(text)]):
                    left = x
                    right = x + w
                    top = y
                    bottom = y + h
                    
                    # jTessBoxEditor用の座標に変換
                    jtess_left, jtess_bottom, jtess_right, jtess_top = self.convert_coordinates_for_jtessboxeditor(
                        left, bottom, right, top, height
                    )
                    
                    char_display = text[i] if i < len(text) else '?'
                    box_line = f"{char_display} {jtess_left} {jtess_bottom} {jtess_right} {jtess_top} 0"
                    box_lines.append(box_line)
            else:
                # 検出輪郭が少ない場合は均等分割でフォールバック
                char_width = width // len(text)
                for i, char in enumerate(text):
                    left = i * char_width
                    right = (i + 1) * char_width
                    top = 10
                    bottom = top + 40
                    
                    jtess_left, jtess_bottom, jtess_right, jtess_top = self.convert_coordinates_for_jtessboxeditor(
                        left, bottom, right, top, height
                    )
                    
                    char_display = ' ' if char == ' ' else char
                    box_line = f"{char_display} {jtess_left} {jtess_bottom} {jtess_right} {jtess_top} 0"
                    box_lines.append(box_line)
            
            with open(output_box_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(box_lines))
            
            return True
            
        except Exception as e:
            print(f"エラー: 適応的box作成に失敗 {image_path}: {e}")
            return False
    
    def copy_image_to_train_dir(self, src_image_path, dest_image_path):
        """
        画像をトレーニングデータディレクトリにコピー
        """
        try:
            shutil.copy2(src_image_path, dest_image_path)
            return True
        except Exception as e:
            print(f"エラー: 画像のコピーに失敗 {src_image_path} -> {dest_image_path}: {e}")
            return False
    
    def generate_training_data(self, use_adaptive=False):
        """
        トレーニングデータを生成する
        """
        print("精密Boxファイル生成を開始します...")
        print(f"入力画像: {self.input_img_dir}")
        print(f"入力テキスト: {self.output_text_dir}")
        print(f"出力先: {self.train_data_dir}")
        print(f"モード: {'適応的' if use_adaptive else '固定位置'}")
        print("-" * 50)
        
        # 画像とテキストのペアを取得
        pairs = self.get_image_text_pairs()
        
        if not pairs:
            print("画像とテキストのペアが見つかりません")
            return
        
        print(f"{len(pairs)}個の画像-テキストペアが見つかりました")
        
        success_count = 0
        
        for pair in pairs:
            base_name = pair['base_name']
            image_file = pair['image_file']
            text_file = pair['text_file']
            
            # パスの構築
            src_image_path = os.path.join(self.input_img_dir, image_file)
            text_file_path = os.path.join(self.output_text_dir, text_file)
            dest_image_path = os.path.join(self.train_data_dir, image_file)
            box_file_path = os.path.join(self.train_data_dir, f"{base_name}.box")
            
            # 正解テキストを読み込み
            ground_truth_text = self.read_ground_truth_text(text_file_path)
            
            if not ground_truth_text:
                print(f"✗ スキップ: {base_name} (テキストが空)")
                continue
            
            # 画像をトレーニングデータディレクトリにコピー
            if not self.copy_image_to_train_dir(src_image_path, dest_image_path):
                continue
            
            # boxファイルを作成
            if use_adaptive:
                success = self.create_adaptive_box_file(src_image_path, ground_truth_text, box_file_path)
            else:
                success = self.create_precise_box_file(src_image_path, ground_truth_text, box_file_path)
            
            if success:
                print(f"✓ 成功: {base_name} -> '{ground_truth_text}'")
                success_count += 1
            else:
                print(f"✗ 失敗: {base_name}")
        
        print("-" * 50)
        print(f"処理完了: {success_count}/{len(pairs)}個のトレーニングデータを生成しました")

def main():
    """
    メイン実行関数
    """
    print("精密Boxファイル生成スクリプト")
    print("=" * 50)
    print("1: 固定位置モード（推奨）")
    print("2: 適応的モード（実験的）")
    
    choice = input("モードを選択 (1 or 2): ").strip()
    
    generator = PreciseBoxFileGenerator()
    
    if choice == "2":
        generator.generate_training_data(use_adaptive=True)
    else:
        generator.generate_training_data(use_adaptive=False)
    
    print("\n🎉 完了！")
    print("提供された座標パターンに基づいてBoxファイルを生成しました")

if __name__ == "__main__":
    main()