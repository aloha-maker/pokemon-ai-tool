# プロジェクト進捗分析レポート

以下は、提供された「要件定義」と「ソースコード」を解析した結果です。

## 機能一覧と実装状況

| 機能要件 | 実装状況 | 担当ファイル・主要関数 |
| :--- | :--- | :--- |
| **F-01 対戦動画学習** | <span style="color:red;">未着手</span> | 関連ファイルなし |
| **F-02 現環境メタ対応パーティ自動生成** | <span style="color:orange;">実装中</span> | `src/ai/party_generator.py` (`PartyGenerator.generate`)<br>`app.py` (`/generate-party`) |
| **F-03 対戦前選出支援** | <span style="color:green;">完了</span> | `src/ai/win_rate_predictor.py` (`WinRatePredictor.predict_best_team`)<br>`app.py` (`/predict`) |
| **F-04 対戦中アクションサジェスト** | <span style="color:orange;">実装中</span> | `src/core/capture.py` (`ScreenCapturer`)<br>`src/core/ocr.py` (`GameStateParser`)<br>`src/ai/predictor.py` (`ActionAIModel.predict_action`)<br>`app.py` (SocketIO `get_suggestion`)<br>`src/main.py` |
| **補助機能：データベース** | <span style="color:orange;">実装中</span> | `data/schema.sql`<br>`scripts/setup_database.py`<br>`src/ai/*.py` (直接 `sqlite3` を使用) |
| **補助機能：UI/UX** | <span style="color:orange;">実装中</span> | `app.py`<br>`templates/index.html`<br>`static/main.js` |

---

## 未実装・実装不十分な機能

### 1. F-01 対戦動画学習
- **状況:** <span style="color:red;">未着手</span>
- **不足点:**
    - 動画ファイルをアップロードまたは指定する機能が存在しません。
    - 動画を解析してポケモン、技、HPなどの情報を抽出するロジック（OpenCV等）が一切実装されていません。
    - 解析結果をデータベースに保存する処理も未実装です。

### 2. F-02 現環境メタ対応パーティ自動生成
- **状況:** <span style="color:orange;">実装中</span>
- **不足点:**
    - `PartyGenerator` クラスのロジックがダミーであり、入力されたポケモンリストからランダムに6体を選ぶだけです。
    - 環境メタや戦術コンセプトを考慮したAIロジックが実装されていません。
    - 運用ガイドも固定のテンプレート文字列を返すのみです。

### 3. F-04 対戦中アクションサジェスト
- **状況:** <span style="color:orange;">実装中</span>
- **不足点:**
    - **リアルタイム連携:** Web UI (`app.py`) 上でのリアルタイム提案機能は、SocketIOのイベント (`get_suggestion`) が用意されているものの、中身はダミーデータを返すだけです。実際のOCRやAI予測と連携されていません。
    - **OCR精度:** `GameStateParser` は実装されていますが、その精度は `roi_config.json` の設定とTesseract-OCRの性能に大きく依存します。現状では動作保証がされていません。
    - **AIモデル:** `ActionAIModel` はタイプ相性のみを考慮した基本的なルールベースAIです。HP、状態異常、相手の交代候補などを考慮した高度な予測ロジックは未実装です。

### 4. 補助機能：データベース
- **状況:** <span style="color:orange;">実装中</span>
- **不足点:**
    - **データアクセス層の欠如:** `src/database/manager.py` や `models.py` が空であり、各機能が直接 `sqlite3` ライブラリを呼び出しています。これにより、コードの再利用性が低く、将来的なDBの変更が困難になります。
    - **スキーマの不整合:** `app.py` で定義されている対戦履歴テーブル (`match_history`) が、公式のスキーマファイル (`data/schema.sql` の `battle_logs`) と異なっており、一貫性がありません。

### 5. 補助機能：UI/UX
- **状況:** <span style="color:orange;">実装中</span>
- **不足点:**
    - 要件にある「近未来デザイン（青/紫ネオン、グラスモーフィズム）」がどの程度実現されているかは不明です。バックエンド機能が先行しており、UIは基本的な要素のみが配置されている可能性が高いです。
    - 対戦分析レポート（勝率グラフ表示など）の専用画面は実装されていないようです。
