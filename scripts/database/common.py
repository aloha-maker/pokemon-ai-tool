import os

# プロジェクトのルートディレクトリを基準にパスを構築
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 主要なディレクトリとファイルのパスを定義
DATA_DIR = os.path.join(BASE_DIR, "data")
MASTER_DATA_DIR = os.path.join(DATA_DIR, "master_data")
DB_PATH = os.path.join(DATA_DIR, "pokemon_ai.db")
SCHEMA_PATH = os.path.join(DATA_DIR, "schema.sql")

# 各マスターCSVファイルのフルパスを定義
POKEMONS_CSV_PATH = os.path.join(MASTER_DATA_DIR, "pokemons.csv")
MOVES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "moves.csv")
TYPES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "types.csv")
ABILITIES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "abilities.csv")
NATURES_CSV_PATH = os.path.join(MASTER_DATA_DIR, "natures.csv")
ITEMS_CSV_PATH = os.path.join(MASTER_DATA_DIR, "items.csv")
