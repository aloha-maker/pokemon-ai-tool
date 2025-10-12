from glob import glob
from config import *
from name_corrector import PokemonNameCorrector, AbilityNameCorrector
from ocr_processor import OCRProcessor
from video_processor import process_video
import os

def main():
    print("動画からの画像抽出＋OCR処理を開始します...")

    # 出力ディレクトリの事前作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    pokemon_corrector = PokemonNameCorrector(POKEMON_MASTER_PATH)
    ability_corrector = AbilityNameCorrector(ABILITY_MASTER_PATH)
    ocr_processor = OCRProcessor(pokemon_corrector, ability_corrector)

    while True:
        video_files = glob(os.path.join(INPUT_DIR, "*.mp4"))
        if not video_files:
            print("\n🎉 全ての動画処理が完了しました。")
            break

        for video_file in video_files:
            process_video(video_file, pokemon_corrector, ability_corrector, ocr_processor)

if __name__ == "__main__":
    main()