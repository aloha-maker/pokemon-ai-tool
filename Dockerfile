# Pythonの公式イメージをベースにする
FROM python:3.13-slim

# タイムゾーン
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# 必須ライブラリ（SRT / RTMP 用）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

# main.pyの実行コマンド
CMD ["python", "app.py"]
