## 作業タイトル
P2-2: `battle_service` の導入

### 現状
- 対戦履歴や動画解析に関するビジネスロジックが、APIルート層 (`routes/api/battle.py`, `routes/api/video.py`) に直接記述されている。
- 特に `battle.py` の `save_battle_result_with_log` など、APIエンドポイント内で複雑なデータ永続化処理が実装されており、責務が分離されていない。
- `video.py` では、バックグラウンドタスクの管理ロジックがAPIルート内にあり、テストが困難である。

### 修正内容
- 新しく `src/services/battle_service.py` を作成する。
- `routes/api/battle.py` と `routes/api/video.py` にあるビジネスロジックを `BattleService` クラスのメソッドとして集約・移管する。
- APIルート層は、リクエストの検証と `BattleService` の呼び出しに専念するようにリファクタリングする。

### 手順
1. `src/services/battle_service.py` を作成し、`BattleService` クラスを定義する。
2. `routes/api/battle.py` から、対戦履歴の取得、新規IDの生成、対戦結果の保存 (`save_battle_result_with_log`) といったロジックを `BattleService` に移管する。
3. `routes/api/video.py` から、動画のアップロード処理、解析タスクの起動、ステータス確認、結果取得のロジックを `BattleService` に移管する。
4. `routes/api/battle.py` と `routes/api/video.py` をリファクタリングし、`BattleService` のメソッドを呼び出すように変更する。
5. `tests/services/test_battle_service.py` を作成し、`BattleService` の主要なメソッド（特に対戦結果保存ロジック）に対する単体テストを記述する。

### 影響範囲
- `src/services/` (新規ファイル `battle_service.py`)
- `src/routes/api/battle.py`
- `src/routes/api/video.py`
- `src/state.py` (動画解析タスクの状態管理部分)
- `tests/services/` (新規ファイル `test_battle_service.py`)

### テスト方法
- `pytest` を使用し、`BattleService` の各メソッドの単体テストを実行する。
- Flaskテストクライアントを使用し、リファクタリング後の `/api/history`, `/api/battles/...`, `/api/videos/...` エンドポイントの結合テストを実行し、APIの挙動に変化がないことを確認する。

### 工数
中

### リスク
- 対戦結果の保存という、データ永続化の根幹に関わる処理を変更するため、デグレードが発生した場合にデータの不整合を招くリスクがある。
- 動画解析の非同期タスク管理のロジックが複雑なため、リファクタリングに際して競合状態などを考慮する必要がある。
