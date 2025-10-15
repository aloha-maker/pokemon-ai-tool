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
