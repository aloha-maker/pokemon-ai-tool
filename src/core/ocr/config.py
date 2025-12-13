import os
import json

# basedir = os.path.abspath(os.path.dirname(__file__))
# 1. 環境変数 'APP_ROOT' を取得。なければ '/app' (Dockerのデフォルト) を使用。
APP_ROOT = os.environ.get('APP_ROOT', '/app')

# ディレクトリ設定
INPUT_DIR = os.path.join(APP_ROOT, '.traindata', 'video', 'input_videos')
OUTPUT_DIR = os.path.join(APP_ROOT, '.traindata', 'text2img')
PROCESSED_DIR = os.path.join(APP_ROOT, '.traindata', 'video', 'processed_videos')
ROI_FILE = os.path.join(APP_ROOT, 'instance', 'roi_config.json')
POKEMON_MASTER_PATH = os.path.join(APP_ROOT, 'data', 'master_data', 'pokemons.csv')
ABILITY_MASTER_PATH = os.path.join(APP_ROOT, 'data', 'master_data', 'abilities.csv')

EXTRACT_PER_SECOND = 1.2  # 1秒に3枚抽出

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

# フェーズ別ROI設定（STAY_ROISからstay_textを削除）
SELECT_ROIS = ['select', 'opponent_name', 'battle_id']
BATTLE_CHOOSE_ROIS = ['my_pokemon_name', 'my_pokemon_hp', 'my_ailment', 
                      'opponent_pokemon_name', 'opponent_pokemon_hp', 'your_ailment']
BATTLE_ACT_ROIS = ['live_comment_row1', 'live_comment_row2', 'my_tokusei_row1', 
                   'my_tokusei_row2', 'terastal', 'terastal_me', 'your_tokusei_row1', 
                   'your_tokusei_row2', 'win_lose']

# 画像マッチング用パス（STAY_TEXT_IMAGEを削除）
START_IMAGE = os.path.join(APP_ROOT, 'static', 'others', 'start.png')
SELECT_IMAGES_PATH = os.path.join(APP_ROOT, 'static', 'others', 'select.png')
WIN_LOSE_IMAGES_DIR = os.path.join(APP_ROOT, 'static', 'others', 'win_lose')
TERA_ICONS_DIR = os.path.join(APP_ROOT, 'static', 'Terastal_icons')
TERA_ME_ICONS_DIR = os.path.join(APP_ROOT, 'static', 'Terastal_icons','me')
AILMENT_ICONS_DIR = os.path.join(APP_ROOT, 'static', 'ailment_icons')

# ROI設定読み込み
with open(ROI_FILE, "r", encoding="utf-8") as f:
    ROI_DICT = json.load(f)


SCRIPT_PATH = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_PATH)))
TESSDATA_DIR = os.path.join(PROJECT_ROOT, "tessdata_custom")

# 環境変数を設定（重要！）
os.environ['TESSDATA_PREFIX'] = TESSDATA_DIR

# カスタム設定（tessdata-dirを削除）
CUSTOM_CONFIG = r"--oem 3 --psm 7"

# TESSDATA_PREFIXを他のモジュールでも使用できるようにエクスポート
TESSDATA_PREFIX = TESSDATA_DIR