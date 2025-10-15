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
