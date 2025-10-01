# JavaScriptファイル分割リファクタリングガイド

## ディレクトリ構造

```
project/
├── static/
│   ├── js/
│   │   ├── main.js              # エントリーポイント
│   │   └── modules/
│   │       ├── utils.js         # 共通ユーティリティ
│   │       ├── formHelpers.js   # フォーム関連ヘルパー
│   │       ├── dashboard.js     # ダッシュボード機能
│   │       ├── partyGenerator.js # パーティ生成機能
│   │       ├── prediction.js    # 選出予測機能
│   │       ├── realtimeAnalysis.js # リアルタイム解析
│   │       ├── videoAnalysis.js # 動画解析機能
│   │       ├── roiEditor.js     # ROI編集機能
│   │       ├── trainedPokemon.js # 育成済みポケモン管理
│   │       ├── partyManagement.js # パーティ管理
│   │       ├── calculator.js    # 計算機能
│   │       ├── simulator.js     # バトルシミュレーター
│   │       └── itemEditor.js    # 持ち物編集機能
│   └── css/
│       └── style.css
└── templates/
    └── index.html
```

## HTMLファイルの変更点

### index.html の `<script>` タグを修正

**変更前:**
```html
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
```

**変更後:**
```html
<script type="module" src="{{ url_for('static', filename='js/main.js') }}"></script>
```

**重要:** `type="module"` を追加することで、ES6のimport/export構文が使用可能になります。

## 各モジュールの役割

### 1. **utils.js** - 共通ユーティリティ
- `escapeHTML()` - HTMLエスケープ
- `showAlert()` - アラート表示
- `debounce()` - 入力遅延処理
- `setButtonLoading()` - ボタンのローディング状態管理

### 2. **formHelpers.js** - フォーム関連
- `populateSelect()` - セレクトボックスの選択肢設定
- `updateAbilitiesForPokemon()` - ポケモンの特性を動的取得
- `initFormSelects()` - マスターデータからフォーム初期化

### 3. **dashboard.js** - ダッシュボード
- 対戦履歴の表示
- 統計情報の可視化

### 4. **partyGenerator.js** - パーティ生成
- AIによるパーティ提案
- 生成パーティの登録

### 5. **prediction.js** - 選出予測
- 相手パーティに対する選出提案
- パーティデータの読み込み
- ポケモン選択UI管理

### 6. **realtimeAnalysis.js** - リアルタイム解析
- WebSocket接続管理
- ゲームウィンドウのキャプチャ
- OCR結果の処理
- AIアドバイスの表示

### 7. **videoAnalysis.js** - 動画解析
- 動画ファイルのアップロード
- 解析タスクの進捗管理
- ポーリングによるステータス更新
- 解析結果の表示

### 8. **roiEditor.js** - ROI編集
- キャンバス描画
- 関心領域の設定・保存
- マウスイベント処理

### 9. **trainedPokemon.js** - 育成済みポケモン管理
- ポケモンリストの表示
- CRUD操作（作成・読込・更新・削除）
- 努力値の合計計算

### 10. **partyManagement.js** - パーティ管理
- パーティのCRUD操作
- メンバー選択UI
- 重複チェック

### 11. **calculator.js** - 計算機能
- ステータス計算
- ダメージ計算
- 確定数計算

### 12. **simulator.js** - バトルシミュレーター
- シミュレーション作成
- 選出画面の管理
- ターン進行処理
- バトル状態の可視化

### 13. **itemEditor.js** - 持ち物編集
- 持ち物のCRUD操作
- マスターデータの更新

## 実装手順

### ステップ1: ディレクトリの作成
```bash
mkdir -p static/js/modules
```

### ステップ2: ファイルの配置
1. 各モジュールファイルを `static/js/modules/` に配置
2. `main.js` を `static/js/` に配置

### ステップ3: HTMLファイルの修正
`templates/index.html` の script タグに `type="module"` を追加

### ステップ4: 動作確認
1. ブラウザの開発者ツールを開く
2. Consoleタブでエラーがないか確認
3. 各機能が正常に動作するか確認

## 注意点

### モジュール化のメリット
- **保守性向上**: 機能ごとに分離され、変更が容易
- **再利用性**: 共通処理を複数の場所で利用可能
- **可読性**: ファイルサイズが小さく、目的が明確
- **テスト容易性**: 個別にテスト可能

### ブラウザ互換性
- モジュール（`type="module"`）はモダンブラウザでのみ動作
- IE11などの古いブラウザでは動作しません
- 必要に応じてwebpackやViteなどのバンドラー使用を検討

### デバッグのヒント
- ブラウザの開発者ツールでソースマップを確認
- `console.log()` で各モジュールの初期化を確認
- ネットワークタブでモジュールの読み込みを確認

## トラブルシューティング

### よくあるエラー

**1. CORS エラー**
```
Access to script at 'file://...' from origin 'null' has been blocked by CORS policy
```
→ ローカルサーバーを使用してください（Flask開発サーバーなど）

**2. モジュールが見つからない**
```
Failed to load module script: Expected a JavaScript module script
```
→ ファイルパスが正しいか確認してください

**3. 循環参照エラー**
```
ReferenceError: Cannot access 'X' before initialization
```
→ モジュール間の依存関係を見直してください

## 今後の拡張

このモジュール構造により、以下の拡張が容易になります：

1. **新機能の追加**: 新しいモジュールを作成して `main.js` でインポート
2. **共通処理の追加**: `utils.js` や `formHelpers.js` に関数を追加
3. **テストの追加**: 各モジュールを個別にテスト可能
4. **ビルドプロセスの導入**: webpack/Viteなどでバンドル・最適化

## まとめ

この分割により、元の1つの大きなファイル（約1300行）が、機能ごとに分離された13のモジュール（各100-300行程度）になりました。これにより保守性と可読性が大幅に向上します。
