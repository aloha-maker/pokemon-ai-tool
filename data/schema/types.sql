-- タイプマスタ
CREATE TABLE IF NOT EXISTS types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ja TEXT
);
