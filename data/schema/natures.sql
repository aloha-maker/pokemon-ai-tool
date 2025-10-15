-- 性格マスタ
CREATE TABLE IF NOT EXISTS natures (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ja TEXT,
    increased_stat TEXT,
    decreased_stat TEXT
);
