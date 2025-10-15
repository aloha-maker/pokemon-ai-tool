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
