-- 新しい構造で一時テーブルを作成
CREATE TABLE parties_log_temp( 
  party_id INTEGER PRIMARY KEY AUTOINCREMENT
  , battle_id TEXT NOT NULL
  , pokemon_id INTEGER NOT NULL
  , pokemon_name TEXT NOT NULL
  , is_opponent BOOLEAN NOT NULL
  , is_selected BOOLEAN NOT NULL
  , is_first BOOLEAN NOT NULL
  , nickname TEXT
  , moves TEXT
  , terastal_type TEXT
  , item TEXT
  , ability TEXT
  , FOREIGN KEY (battle_id) REFERENCES battles(battle_id)
);

-- データを移行
-- 既存のデータを移行（新しいカラムにはNULLまたはデフォルト値を設定）
INSERT INTO parties_log_temp 
(
  party_id, 
  battle_id, 
  pokemon_id, 
  pokemon_name, 
  is_opponent, 
  is_selected,
  is_first,
  nickname,
  moves,
  terastal_type,
  item,
  ability
)
SELECT 
  pal.party_id, 
  pal.battle_id, 
  pal.pokemon_id, 
  pal.pokemon_name, 
  pal.is_opponent, 
  pal.is_selected,
  false as is_first,
  pol.nickname,
  pol.moves,
  pol.terastal_type,
  pol.item,
  pol.ability
FROM parties_log pal
LEFT OUTER JOIN pokemons_log pol on pol.pokemon_id = pal.pokemon_id
;

-- 元のテーブルを削除
DROP TABLE parties_log;

-- 新しいテーブルにリネーム
ALTER TABLE parties_log_temp RENAME TO parties_log;

-- その後でpokemons_logを削除
DROP TABLE pokemons_log;