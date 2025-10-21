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
