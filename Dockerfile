# Pythonの公式イメージをベースにする
FROM python:3.13-slim

# タイムゾーン
RUN ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime
# apt
RUN apt update
RUN apt install -y libopencv-dev

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

# main.pyの実行コマンド
CMD ["python", "app.py"]
