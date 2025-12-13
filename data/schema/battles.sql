-- 対戦ログ（正規化版）
CREATE TABLE IF NOT EXISTS battles (
    battle_id TEXT PRIMARY KEY,
    battle_date TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    season INTEGER,
    regulation TEXT,
    battle_format TEXT NOT NULL CHECK(battle_format IN ('シングル', 'ダブル')),
    my_rank INTEGER,
    opponent_rank INTEGER,
    result TEXT NOT NULL CHECK(result IN ('win', 'lose', 'unknown')),
    my_first_pokemon TEXT,
    opponent_first_pokemon TEXT,
    memo TEXT
);
