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
    name_ja TEXT,
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

-- タイプマスタ
CREATE TABLE IF NOT EXISTS types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ja TEXT
);

-- 特性マスタ
CREATE TABLE IF NOT EXISTS abilities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ja TEXT
);

-- 性格マスタ
CREATE TABLE IF NOT EXISTS natures (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ja TEXT,
    increased_stat TEXT,
    decreased_stat TEXT
);

-- 持ち物マスタ
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ja TEXT
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
    result TEXT DEFAULT 'unknown' NOT NULL CHECK(result IN ('win', 'lose', 'unknown')),
    opponent_party TEXT, -- JSON format
    my_party_id INTEGER,
    battle_data TEXT, -- JSON format for turn-by-turn log
    video_task_id TEXT, -- 動画解析タスクのID
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

-- F-05: 育成済みポケモン管理テーブル
CREATE TABLE IF NOT EXISTS trained_pokemons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER NOT NULL, -- pokemons.csv のID
    nickname TEXT,
    level INTEGER NOT NULL DEFAULT 50,
    tera_type_id INTEGER, -- types.csv のID
    ability_id INTEGER, -- abilities.csv のID
    nature_id INTEGER, -- natures.csv のID
    held_item_id INTEGER, -- items.csv のID
    move1_id INTEGER, -- moves.csv のID
    move2_id INTEGER,
    move3_id INTEGER,
    move4_id INTEGER,
    ev_hp INTEGER DEFAULT 0,
    ev_atk INTEGER DEFAULT 0,
    ev_def INTEGER DEFAULT 0,
    ev_spa INTEGER DEFAULT 0,
    ev_spd INTEGER DEFAULT 0,
    ev_spe INTEGER DEFAULT 0,
    iv_hp INTEGER DEFAULT 31,
    iv_atk INTEGER DEFAULT 31,
    iv_def INTEGER DEFAULT 31,
    iv_spa INTEGER DEFAULT 31,
    iv_spd INTEGER DEFAULT 31,
    iv_spe INTEGER DEFAULT 31,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pokemon_id) REFERENCES pokemons(id),
    FOREIGN KEY (tera_type_id) REFERENCES types(id),
    FOREIGN KEY (ability_id) REFERENCES abilities(id),
    FOREIGN KEY (nature_id) REFERENCES natures(id),
    FOREIGN KEY (held_item_id) REFERENCES items(id),
    FOREIGN KEY (move1_id) REFERENCES moves(id),
    FOREIGN KEY (move2_id) REFERENCES moves(id),
    FOREIGN KEY (move3_id) REFERENCES moves(id),
    FOREIGN KEY (move4_id) REFERENCES moves(id)
);
