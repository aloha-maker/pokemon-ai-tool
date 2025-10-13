# test_ocr_processor.py
import os
import cv2
from glob import glob
import pandas as pd
from config import POKEMON_MASTER_PATH, ABILITY_MASTER_PATH
from name_corrector import PokemonNameCorrector, AbilityNameCorrector
from ocr_roi_processor import OCRROIProcessor

class TestOCRProcessor:
    def __init__(self, output_dir):
        self.pokemon_corrector = PokemonNameCorrector(POKEMON_MASTER_PATH)
        self.ability_corrector = AbilityNameCorrector(ABILITY_MASTER_PATH)
        self.ocr_processor = OCRROIProcessor(output_dir, self.pokemon_corrector, self.ability_corrector)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def process_image_folder(self, input_folder, output_csv="test_ocr_results.csv"):
        """
        切り取られた画像フォルダを一括処理
        
        Args:
            input_folder: 切り取られた画像が保存されているフォルダ
            output_csv: 出力CSVファイル名
        """
        print(f"🔍 テストOCR処理開始: {input_folder}")
        
        # 画像ファイルを取得
        image_files = glob(os.path.join(input_folder, "*.png")) + glob(os.path.join(input_folder, "*.jpg"))
        
        if not image_files:
            print("❌ 処理対象の画像ファイルが見つかりません")
            return
        
        results = []
        
        for image_path in image_files:
            result = self._process_single_image(image_path)
            if result:
                results.append(result)
        
        # CSVに保存
        if results:
            df = pd.DataFrame(results)
            csv_path = os.path.join(self.output_dir, output_csv)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"✅ 結果を保存: {csv_path} (全{len(results)}件)")
        
        return results
    
    def _process_single_image(self, image_path):
        """
        単一画像を処理
        
        Returns:
            dict: 認識結果を含む辞書
        """
        try:
            # 画像読み込み
            image = cv2.imread(image_path)
            if image is None:
                print(f"❌ 画像読み込み失敗: {image_path}")
                return None
            
            # ファイル名からROI名を推測
            filename = os.path.basename(image_path)
            roi_name = self._guess_roi_name(filename)
            
            # OCR実行
            text, confidence = self.ocr_processor.extract_text_from_image(image, roi_name)
            
            # 名前補正（テスト用なので閾値チェックなし）
            corrected_text = self._apply_correction_for_test(text, roi_name)
            
            # 類似度計算（テスト用）
            similarity_score = self._calculate_similarity(text, corrected_text, roi_name)
            
            result = {
                'image_file': filename,
                'roi_name': roi_name,
                'original_text': text,
                'corrected_text': corrected_text,
                'similarity_score': similarity_score,
                'confidence_max': confidence['max'],
                'confidence_median': confidence['median'],
                'confidence_avg': confidence['avg'],
                'image_path': image_path
            }
            
            # コンソール出力
            print(f"📊 {filename}:")
            print(f"  - 元のテキスト: '{text}'")
            print(f"  - 補正テキスト: '{corrected_text}'")
            print(f"  - 類似度: {similarity_score:.3f}")
            print(f"  - 確信度: 最大{confidence['max']:.1f}, 平均{confidence['avg']:.1f}")
            
            return result
            
        except Exception as e:
            print(f"❌ 処理エラー ({image_path}): {e}")
            return None
    
    def _guess_roi_name(self, filename):
        """
        ファイル名からROI名を推測
        """
        filename_lower = filename.lower()
        
        if 'pokemon' in filename_lower or 'poke' in filename_lower:
            if 'my' in filename_lower or '自分' in filename_lower:
                return 'my_pokemon_name'
            elif 'opponent' in filename_lower or '相手' in filename_lower:
                return 'opponent_pokemon_name'
            else:
                return 'my_pokemon_name'  # デフォルト
        
        elif 'ability' in filename_lower or 'tokusei' in filename_lower or '特性' in filename_lower:
            if 'my' in filename_lower or '自分' in filename_lower:
                return 'my_tokusei_row2'
            elif 'opponent' in filename_lower or '相手' in filename_lower:
                return 'your_tokusei_row2'
            else:
                return 'my_tokusei_row2'  # デフォルト
        
        elif 'comment' in filename_lower or '実況' in filename_lower:
            return 'live_comment_row1'
        
        elif 'battle' in filename_lower or 'バトル' in filename_lower:
            return 'battle_id'
        
        else:
            return 'unknown'
    
    def _apply_correction_for_test(self, text, roi_name):
        """
        テスト用の名前補正（閾値チェックなし）
        """
        if not text:
            return text
            
        if roi_name in ['my_pokemon_name', 'opponent_pokemon_name']:
            # ポケモン名補正（閾値チェックなし）
            return self.pokemon_corrector.find_closest_name(text, threshold=0.0)
        
        elif roi_name in ['my_tokusei_row2', 'your_tokusei_row2']:
            # 特性名補正（閾値チェックなし）
            return self.ability_corrector.find_closest_name(text, threshold=0.0)
        
        else:
            return text
    
    def _calculate_similarity(self, original_text, corrected_text, roi_name):
        """
        元のテキストと補正テキストの類似度を計算
        """
        if not original_text or not corrected_text:
            return 0.0
        
        if original_text == corrected_text:
            return 1.0
        
        # 簡易的な類似度計算
        from difflib import SequenceMatcher
        return SequenceMatcher(None, original_text, corrected_text).ratio()

def main():
    """
    テスト処理のメイン関数
    """
    # 設定
    INPUT_FOLDER = r'C:\pokemon-ai-tool\.traindata\text2img\test_1013\my_pokemon_name'  # 切り取られた画像があるフォルダ
    OUTPUT_DIR = r'C:\pokemon-ai-tool\.traindata\text2img\test_1013'   # 結果出力フォルダ
    OUTPUT_CSV = "ocr_test_results.csv"
    
    # プロセッサー初期化
    processor = TestOCRProcessor(OUTPUT_DIR)
    
    # 処理実行
    results = processor.process_image_folder(INPUT_FOLDER, OUTPUT_CSV)
    
    if results:
        print(f"\n🎉 テスト処理完了: {len(results)}件の画像を処理")
        
        # 統計情報の表示
        df = pd.DataFrame(results)
        print("\n📈 統計情報:")
        print(f"  - 平均確信度: {df['confidence_avg'].mean():.2f}")
        print(f"  - 平均類似度: {df['similarity_score'].mean():.2f}")
        print(f"  - 最低確信度: {df['confidence_avg'].min():.2f}")
        print(f"  - 最高確信度: {df['confidence_avg'].max():.2f}")

if __name__ == "__main__":
    main()