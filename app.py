from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # index.htmlをレンダリングして返す
    return render_template('index.html')

if __name__ == '__main__':
    # デバッグモードでアプリケーションを起動
    app.run(debug=True)
