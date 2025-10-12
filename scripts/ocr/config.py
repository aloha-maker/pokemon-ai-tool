import os
import json

# ディレクトリ設定
INPUT_DIR = r'C:\pokemon-ai-tool\.traindata\video\input_videos'
OUTPUT_DIR = r'C:\pokemon-ai-tool\.traindata\text2img'
PROCESSED_DIR = r'C:\pokemon-ai-tool\.traindata\video\processed_videos'
ROI_FILE = r'C:\pokemon-ai-tool\instance\roi_config.json'
POKEMON_MASTER_PATH = r'C:\pokemon-ai-tool\data\master_data\pokemons.csv'
ABILITY_MASTER_PATH = r'C:\pokemon-ai-tool\data\master_data\abilities.csv'

EXTRACT_PER_SECOND = 0.3  # 1秒に3枚抽出

# ROIカテゴリ設定
OCR_EXEMPT_ROIS = {'your_ailment', 'my_ailment', 'my_pokemon_hp', 'opponent_pokemon_hp'}
SKIP_ROIS = {'your_party'} | {f'your_poke{i}' for i in range(1, 7)}
POKEMON_NAME_ROIS = {'my_pokemon_name', 'opponent_pokemon_name'}
HP_ROIS = {'my_pokemon_hp', 'opponent_pokemon_hp'}
AILMENT_ROIS = {'my_ailment', 'your_ailment'}
OTHER_ROIS = {'live_comment_row1', 'live_comment_row2',
              'my_tokusei_row1', 'my_tokusei_row2',
              'your_tokusei_row1', 'your_tokusei_row2'}
ABILITY_NAME_ROIS = {'my_tokusei_row2', 'your_tokusei_row2'}
POKEMON_NO_ROIS = {'my_tokusei_row1', 'your_tokusei_row1'}

# ROI設定読み込み
with open(ROI_FILE, "r", encoding="utf-8") as f:
    ROI_DICT = json.load(f)

# Tesseract設定
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRIPT_PATH = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_PATH)))
TESSDATA_DIR = os.path.join(PROJECT_ROOT, "tessdata_custom")
CUSTOM_CONFIG = f"--tessdata-dir {TESSDATA_DIR} --oem 3 --psm 7"
