## 作業タイトル
P2-2: `DatabaseManager` の責務分離

### 現状
- `src/database/manager.py` の `DatabaseManager` クラスが、単純なCRUD操作（データアクセス層の責務）に加え、複雑な分析・集計クエリ（ビジネスロジック層の責務）まで担当しており、肥大化している（神クラス化）。
- `get_win_rate_by_opponent` や `get_selection_pattern_win_rate` といったメソッドは、高度なビジネス知識を必要とする。

### 修正内容
- サービスレイヤーの導入（P2-1）に伴い、`DatabaseManager` が抱えているビジネスロジックを適切なサービスクラスに移管する。
- `DatabaseManager` を、SQLAlchemyのセッションを管理し、基本的なCRUD操作を提供する純粋なデータアクセス層（リポジトリパターンに近い役割）に特化させる。

### 手順
1. P2-1で作成したサービスクラス（例: `DashboardService`）を特定する。
2. `DatabaseManager` から、分析・集計系のメソッド（`get_win_rate_by_opponent` など）を `DashboardService` に移管する。
3. 移管されたメソッド内で `DatabaseManager` のより基本的なメソッド（`find_all`, `execute_query`など）を呼び出すようにリファクタリングする。
4. `DatabaseManager` には、テーブルごとの基本的なCRUD操作（`add`, `get`, `update`, `delete`）や、単純な検索メソッドのみが残るように整理する。
5. 関連するテストコードを修正・追加する。

### 影響範囲
- `src/database/manager.py`
- `src/services/` 配下のサービスクラス
- `src/routes/api/` 配下の全ファイル（間接的に影響）
- `tests/`

### テスト方法
- `DatabaseManager` の単体テストを修正し、純粋なデータアクセス機能のみをテストするようにする。
- ビジネスロジックを移管したサービスクラスの単体テストで、分析・集計ロジックが正しく動作することを確認する。
- APIの結合テストを実行し、リファクタリング前と挙動が変わらないことを確認する。

### 工数
中

### リスク
- データベース関連のロジック変更は、データの不整合やパフォーマンス劣化に繋がるリスクがある。
- **前提条件:** `DatabaseManager` と関連サービスに対する十分な単体テストが存在すること。

### DashboardService移管対象メソッドリスト:

   * get_dashboard_summary(): ダッシュボードのサマリー情報（勝率、ランク推移など）を取得する。
   * get_opponent_pokemon_ranking(): 相手のパーティによく含まれるポケモンのランキングを取得する。
   * get_win_rate_by_opponent(): 相手のポケモンごとの勝率を計算する。
   * get_my_pokemon_selection_rate(): 自分のポケモンの選出率を計算する。
   * get_selection_pattern_win_rate(): 自分の選出パターン（3体）ごとの勝率を計算する。
   * get_opponent_pokemon_customization_ranking():
     指定された相手ポケモンの技、持ち物、テラスタイプの採用率ランキングを取得する。
   * get_battle_stats(): 全体の対戦数や勝利数などの基本的な統計データを取得する。


### BattleService に移管すべきメソッド
  対戦の履歴やログの記録・取得に関連するメソッドです。
   * get_battle_history()
   * get_battle_log_by_id()
   * get_all_battle_logs()
   * get_latest_battle_id_for_today()
   * add_battle_log_from_video()
   * save_battle_result_with_log()

  ### TrainedPokemonService に移管すべきメソッド
  ユーザーが育成した個々のポケモン（育成済みポケモン）のCRUD操作に関連するメソッドです。
   * get_all_trained_pokemons()
   * get_trained_pokemon_by_id()
   * add_trained_pokemon()
   * update_trained_pokemon()
   * delete_trained_pokemon()

  ### PartyService に移管すべきメソッド
  育成済みポケモンで構成される「パーティ」のCRUD操作に関連するメソッドです。
   * get_all_parties()
   * get_party_by_id()
   * add_party()
   * update_party()
   * delete_party()
   * get_party_pokemon_names()

  ### MasterDataService に移管すべきメソッド
  ポケモン、技、特性などのマスターデータを取得するためのメソッドです。
   * get_pokemon_by_name()
   * get_move_by_name()
   * get_pokemons_by_names()
   * get_master_data_by_resource()
   * get_abilities_by_pokemon_id()
   * get_moves_by_pokemon_id()
   * get_moves_by_type()

  ### DatabaseManager に残す、または汎用DBサービスに移管するメソッド
  テーブル横断的な汎用検索機能などです。
   * get_all_tables()
   * search_table()