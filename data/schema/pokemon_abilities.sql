-- ポケモンと特性の中間テーブル
CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    is_hidden BOOLEAN NOT NULL DEFAULT 0, -- かくれ特性かどうか
    PRIMARY KEY (pokemon_id, ability_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemons (id) ON DELETE CASCADE,
    FOREIGN KEY (ability_id) REFERENCES abilities (id) ON DELETE CASCADE
);
