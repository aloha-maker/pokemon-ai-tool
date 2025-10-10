# src/extensions.py
from flask_executor import Executor

# アプリケーションの循環参照を避けるため、拡張機能のインスタンスをここで生成します。
# アプリケーションインスタンスとの紐付けは、app factory内で行います。
executor = Executor()
