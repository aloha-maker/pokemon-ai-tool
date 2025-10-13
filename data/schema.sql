-- 既存のテーブルがあれば削除（再構築用）
DROP TABLE IF EXISTS pokemons;
DROP TABLE IF EXISTS moves;
DROP TABLE IF EXISTS parties;
DROP TABLE IF EXISTS party_members;
DROP TABLE IF EXISTS battle_logs;
DROP TABLE IF EXISTS analysis_results;
DROP TABLE IF EXISTS raw_battle_events;

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
    name_ja TEXT,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    power INTEGER,
    accuracy INTEGER,
    pp INTEGER
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

-- ポケモンと特性の中間テーブル
CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT 0, -- かくれ特性かどうか
    PRIMARY KEY (pokemon_id, ability_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemons (id) ON DELETE CASCADE,
    FOREIGN KEY (ability_id) REFERENCES abilities (id) ON DELETE CASCADE
);

-- F-06: パーティ管理テーブル
CREATE TABLE IF NOT EXISTS parties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- F-06: パーティ構成員テーブル
CREATE TABLE IF NOT EXISTS party_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    party_id INTEGER NOT NULL,
    trained_pokemon_id INTEGER NOT NULL,
    member_index INTEGER NOT NULL, -- パーティ内の順番 (0-5)
    UNIQUE (party_id, trained_pokemon_id),
    UNIQUE (party_id, member_index),
    FOREIGN KEY (party_id) REFERENCES parties (id) ON DELETE CASCADE,
    FOREIGN KEY (trained_pokemon_id) REFERENCES trained_pokemons (id) ON DELETE CASCADE
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
    FOREIGN KEY (my_party_id) REFERENCES parties (id) ON DELETE SET NULL
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

CREATE TABLE IF NOT EXISTS pokemons_log (
    pokemon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_name TEXT NOT NULL,
    nickname TEXT,
    moves TEXT,
    terastal_type TEXT,
    item TEXT,
    ability TEXT,
    UNIQUE(pokemon_name, nickname, moves, terastal_type, item, ability)
);

CREATE TABLE IF NOT EXISTS parties_log (
    party_id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id TEXT NOT NULL,
    pokemon_id INTEGER,
    pokemon_name TEXT NOT NULL,
    is_opponent BOOLEAN NOT NULL,
    is_selected BOOLEAN NOT NULL,
    FOREIGN KEY (battle_id) REFERENCES battles (battle_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemons_log (pokemon_id)
);

-- OCRによる生ログ（時系列、正規化版）
CREATE TABLE raw_battle_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    log_timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
    roi_name TEXT NOT NULL,
    ocr_text TEXT,
    FOREIGN KEY (battle_id) REFERENCES battles (battle_id),
    UNIQUE(battle_id, sequence, roi_name)
);


