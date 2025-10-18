-- OCRによる生ログ（時系列、正規化版）
CREATE TABLE raw_battle_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    log_timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
    roi_name TEXT NOT NULL,
    ocr_text TEXT,
    phase TEXT,
    FOREIGN KEY (battle_id) REFERENCES battles (battle_id),
    UNIQUE(battle_id, sequence, roi_name)
);