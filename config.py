# config.py
import os
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///C:/pokemon-ai-tool/data/pokemon_ai.db'
    DATABASE_URL = SQLALCHEMY_DATABASE_URI
    TESSERACT_PATH = os.environ.get('TESSERACT_PATH')
    ROI_CONFIG_PATH = os.path.join(basedir, 'instance', 'roi_config.json')
    TYPE_CHART_PATH = os.path.join(basedir, 'instance', 'type_chart.json')
    # ... 他の共通設定
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'echo': True  # デバッグ用にSQLを表示
    }


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'  # インメモリDBを使用
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
