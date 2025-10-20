-- ポケモン図鑑テーブル
CREATE TABLE IF NOT EXISTS pokemons (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ja TEXT,
    base_id INTEGER,
    type1 TEXT NOT NULL,
    type2 TEXT,
    hp INTEGER NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    sp_attack INTEGER NOT NULL,
    sp_defense INTEGER NOT NULL,
    speed INTEGER NOT NULL,
    moves TEXT,
    abilities TEXT
);

CREATE INDEX IF NOT EXISTS idx_pokemons_name_ja ON pokemons (name_ja);
