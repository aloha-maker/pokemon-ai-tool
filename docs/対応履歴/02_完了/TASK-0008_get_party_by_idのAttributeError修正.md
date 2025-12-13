# 【対応履歴フォーマット】
## 作業タイトル
`get_party_by_id`実行時の`AttributeError`修正

### 現状
`get_party_by_id`メソッド内で、存在しない`_get_party_members`メソッドを呼び出しているため、API `/api/party/<party_id>` が `AttributeError` でクラッシュする。
これは、`TASK-0006` のN+1クエリ解消リファクタリングで `_get_party_members` が削除されたことに起因する。

### 修正内容
`database/manager.py` の `get_party_by_id` メソッドを修正し、N+1クエリを発生させない効率的な方法でパーティメンバーを取得するように変更する。
具体的には、`get_parties`メソッドと同様のJOINを用いた一括取得ロジックを参考に、指定された `party_id` に紐づくメンバー情報を取得する。

### 手順
1. `C:\pokemon-ai-tool\docs\対応履歴\00_未着手` に `TASK-0008_get_party_by_idのAttributeError修正.md` を作成する。
2. `src/database/manager.py` を開き、`get_party_by_id` メソッドを修正する。
3. 修正後の`get_party_by_id`が、パーティ情報とメンバー情報を正しく取得できることを確認するためのテストコードを `tests/database/test_manager.py` に追加または修正する。
4. `pytest` を実行し、すべてのテストが成功することを確認する。

### 影響範囲
- `/api/party/<party_id>` APIエンドポイント
- `src/database/manager.py`
- `tests/database/test_manager.py`

### テスト方法
1. `pytest tests/database/test_manager.py` を実行し、`get_party_by_id` に関連するテストが成功することを確認する。
2. (手動) Flaskサーバーを起動し、Postmanやcurlなどで `/api/party/1` のようなエンドポイントにアクセスし、パーティ情報とメンバー情報が正しく返却されることを確認する。

### 工数
0.5h

### リスク
なし。既存の修正漏れを対応するものであり、デグレードのリスクは低い。
