# src/extensions.py
from flask_executor import Executor
from flask_sqlalchemy import SQLAlchemy

# アプリケーションの循環参照を避けるため、拡張機能のインスタンスをここで生成します。
# アプリケーションインスタンスとの紐付けは、app factory内で行います。
executor = Executor()
db = SQLAlchemy()
