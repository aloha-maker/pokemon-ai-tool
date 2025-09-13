-- 既存のテーブルがあれば削除（再構築用）
DROP TABLE IF EXISTS pokemons;
DROP TABLE IF EXISTS moves;
DROP TABLE IF EXISTS parties;
DROP TABLE IF EXISTS party_members;
DROP TABLE IF EXISTS battle_logs;
DROP TABLE IF EXISTS analysis_results;

-- ポケモン図鑑テーブル
CREATE TABLE pokemons (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type1 TEXT NOT NULL,
    type2 TEXT,
    hp INTEGER NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    sp_attack INTEGER NOT NULL,
    sp_defense INTEGER NOT NULL,
    speed INTEGER NOT NULL
);

-- 技テーブル
CREATE TABLE moves (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    power INTEGER,
    accuracy INTEGER
);

-- 構築済みパーティテーブル
CREATE TABLE parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    concept TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);

-- パーティ構成員テーブル
CREATE TABLE party_members (
    party_id INTEGER NOT NULL,
    pokemon_id INTEGER NOT NULL,
    item TEXT,
    ability TEXT,
    teras_type TEXT,
    ev_hp INTEGER DEFAULT 0,
    ev_attack INTEGER DEFAULT 0,
    ev_defense INTEGER DEFAULT 0,
    ev_sp_attack INTEGER DEFAULT 0,
    ev_sp_defense INTEGER DEFAULT 0,
    ev_speed INTEGER DEFAULT 0,
    move1_id INTEGER,
    move2_id INTEGER,
    move3_id INTEGER,
    move4_id INTEGER,
    PRIMARY KEY (party_id, pokemon_id),
    FOREIGN KEY (party_id) REFERENCES parties (id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemons (id),
    FOREIGN KEY (move1_id) REFERENCES moves (id),
    FOREIGN KEY (move2_id) REFERENCES moves (id),
    FOREIGN KEY (move3_id) REFERENCES moves (id),
    FOREIGN KEY (move4_id) REFERENCES moves (id)
);

-- 対戦履歴テーブル
CREATE TABLE battle_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result TEXT NOT NULL CHECK(result IN ('win', 'lose')),
    opponent_party TEXT, -- JSON format
    my_party_id INTEGER NOT NULL,
    battle_data TEXT, -- JSON format for turn-by-turn log
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    FOREIGN KEY (my_party_id) REFERENCES parties (id)
);

-- AIによる分析結果テーブル
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER NOT NULL UNIQUE,
    win_factor TEXT,
    lose_factor TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
    FOREIGN KEY (log_id) REFERENCES battle_logs (id)
);
