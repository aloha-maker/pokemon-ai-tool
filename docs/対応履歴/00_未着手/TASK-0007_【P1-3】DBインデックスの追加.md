### 3.3. 【P1-3】DBインデックスの追加

*   **目的:** `JOIN` や `WHERE` 句で頻繁に使用されるカラムにインデックスを追加し、データベースの検索パフォーマンスを向上させる。
*   **想定工数:** 3時間

#### 3.3.1. 詳細修正手順

1.  **インデックス対象の特定:** `parties_log(battle_id)` や `trained_pokemons(pokemon_id)`、`party_members(party_id, pokemon_id)` など、外部キーとして利用されているカラムをリストアップします。
2.  **インデックス作成SQLの作成:**
    *   `CREATE INDEX idx_parties_log_battle_id ON parties_log (battle_id);`
    *   `CREATE INDEX idx_trained_pokemons_pokemon_id ON trained_pokemons (pokemon_id);`
3.  **スキーマ更新スクリプトの作成:**
    *   `scripts/apply_schema_updates.py` のようなスクリプトを作成し、既存のデータベースにインデックスを追加できるようにします。このスクリプトは冪等性（何度実行しても同じ結果になること）を保つようにします。

#### 3.3.2. コード例

**`scripts/apply_schema_updates.py` (新規作成)**
```python
import sqlite3

def add_indexes(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    indexes = {
        "idx_parties_log_battle_id": "CREATE INDEX IF NOT EXISTS idx_parties_log_battle_id ON parties_log (battle_id);",
        "idx_trained_pokemons_pokemon_id": "CREATE INDEX IF NOT EXISTS idx_trained_pokemons_pokemon_id ON trained_pokemons (pokemon_id);"
    }

    for name, sql in indexes.items():
        try:
            print(f"Creating index {name}...")
            cursor.execute(sql)
        except Exception as e:
            print(f"Failed to create index {name}: {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_indexes('instance/database.db')
```

#### 3.3.3. 影響範囲

*   データベーススキーマのみ。アプリケーションコードへの変更はありません。
*   書き込みパフォーマンスがわずかに低下する可能性がありますが、読み取りパフォーマンスの向上がそれを上回る見込みです。

#### 3.3.4. テスト方法

*   インデックス追加前後で、対象のクエリ（例: 特定の`battle_id`を持つログの取得）の実行時間を比較し、パフォーマンスが改善していることを確認します。
*   `EXPLAIN QUERY PLAN` を使用して、クエリがインデックスを使用するようになったことを確認します。

#### 3.3.5. リスクと対策

*   **リスク:** 不適切なインデックスは、かえってパフォーマンスを悪化させる可能性があります。
*   **対策:** 実際のアプリケーションで使われているクエリを分析し、最も効果的なカラムにのみインデックスを追加します。