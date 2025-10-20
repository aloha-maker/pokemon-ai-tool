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

CREATE INDEX IF NOT EXISTS idx_parties_log_battle_id ON parties_log (battle_id);
CREATE INDEX IF NOT EXISTS idx_parties_log_opponent_pokemon ON parties_log (is_opponent, pokemon_name);