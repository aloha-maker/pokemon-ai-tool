from flask import Flask, render_template, request, jsonify
import json
import sqlite3
import os

app = Flask(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'pokemon_ai.db')

def init_db():
    """Initializes the database and creates the match_history table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            my_party TEXT,
            opponent_party TEXT,
            my_selection TEXT,
            result TEXT,
            created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()

@app.route('/')
def index():
    # index.htmlをレンダリングして返す
    return render_template('index.html')

# 【仮設】対戦結果を保存するためのAPIエンドポイント
@app.route('/api/history/add', methods=['POST'])
def add_history():
    data = request.json
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO match_history (my_party, opponent_party, my_selection, result) VALUES (?, ?, ?, ?)",
            (
                json.dumps(data['my_party']),
                json.dumps(data['opponent_party']),
                json.dumps(data['my_selection']),
                data['result']
            )
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "対戦履歴を保存しました。"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 対戦履歴と分析データを取得するAPIエンドポイント
@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 履歴一覧を取得
        cursor.execute("SELECT * FROM match_history ORDER BY created_at DESC LIMIT 50")
        raw_history = [dict(row) for row in cursor.fetchall()]

        # 統計データを計算
        cursor.execute("SELECT COUNT(*) as total FROM match_history")
        total_matches = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as wins FROM match_history WHERE result = 'win'")
        total_wins = cursor.fetchone()['wins']

        win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0

        conn.close()

        return jsonify({
            "raw_history": raw_history,
            "stats": {
                "total_matches": total_matches,
                "total_wins": total_wins,
                "win_rate": round(win_rate, 1)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    # デバッグモードでアプリケーションを起動
    app.run(debug=True)
