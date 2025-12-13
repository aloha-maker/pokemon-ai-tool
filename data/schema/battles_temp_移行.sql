SELECT name FROM sqlite_master 
WHERE type = 'table' AND sql LIKE '%REFERENCES battles%';

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
FROM parties_log

-- 元のテーブルを削除
DROP TABLE parties_log;
ALTER TABLE parties_log_temp RENAME TO parties_log;


-- 新しい構造で一時テーブルを作成
CREATE TABLE raw_battle_events_temp( 
  event_id INTEGER PRIMARY KEY AUTOINCREMENT
  , battle_id TEXT NOT NULL
  , sequence INTEGER NOT NULL
  , log_timestamp TEXT NOT NULL DEFAULT ( 
    strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')
  ) 
  , roi_name TEXT NOT NULL
  , ocr_text TEXT
  , phase TEXT
  , FOREIGN KEY (battle_id) REFERENCES battles (battle_id)
  , UNIQUE (battle_id, sequence, roi_name)
)
-- データを移行
INSERT INTO raw_battle_events_temp 
(
  event_id
  , battle_id
  , sequence
  , log_timestamp
  , roi_name
  , ocr_text
  , phase
)
SELECT 
  event_id
  , battle_id
  , sequence
  , log_timestamp
  , roi_name
  , ocr_text
  , phase
FROM raw_battle_events

-- 元のテーブルを削除
DROP TABLE raw_battle_events;
ALTER TABLE raw_battle_events_temp RENAME TO raw_battle_events;

-- バックアップ
ALTER TABLE battles RENAME TO battles_temp1;

-- 新しい構造で一時テーブルを作成
CREATE TABLE battles( 
  battle_id TEXT PRIMARY KEY
  , battle_date TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
  , season INTEGER
  , regulation TEXT
  , battle_format TEXT NOT NULL CHECK (battle_format IN ('シングル', 'ダブル'))
  , my_rank INTEGER
  , opponent_rank INTEGER
  , result TEXT NOT NULL CHECK (result IN ('win', 'lose', 'unknown'))
  , memo TEXT
)


-- データを移行
-- 既存のデータを移行（新しいカラムにはNULLまたはデフォルト値を設定）
INSERT INTO battles
(
  battle_id, 
  battle_date, 
  season, 
  regulation, 
  battle_format, 
  my_rank,
  opponent_rank,
  result,
  memo
)
SELECT 
  battle_id, 
  battle_date, 
  season, 
  regulation, 
  battle_format, 
  my_rank,
  opponent_rank,
  result,
  memo
FROM battles_temp1
;

-- バックアップのテーブルを削除
DROP TABLE battles_temp1;