-- 対戦履歴テーブル
CREATE TABLE battle_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result TEXT DEFAULT 'unknown' NOT NULL CHECK(result IN ('win', 'lose', 'unknown')),
    opponent_party TEXT, -- JSON format
    my_party_id INTEGER,
    battle_data TEXT, -- JSON format for turn-by-turn log
    video_task_id TEXT, -- 動画解析タスクのID
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    FOREIGN KEY (my_party_id) REFERENCES parties (id) ON DELETE SET NULL
);
