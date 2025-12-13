-- AIによる分析結果テーブル
CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER NOT NULL UNIQUE,
    win_factor TEXT,
    lose_factor TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    FOREIGN KEY (log_id) REFERENCES battle_logs (id)
);