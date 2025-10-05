# 機能設計書: F-09 対戦選出画面からの相手パーティ自動読み取り

## 1. 概要

本機能は、リアルタイム解析中の対戦選出画面から、ボタン一つで相手パーティのポケモン6体を自動的に認識し、選出予測UIの相手パーティ欄にその名前を自動入力するものである。
これにより、ユーザーの手入力の手間を大幅に削減し、より迅速な対戦準備を支援する。

## 2. UI/UX設計

### 2.1. ボタンの追加

- **場所:** `index.html` の「相手パーティ」セクションのヘッダー部分。既存の「パーティ保存」「予測を開始」ボタンの隣に配置する。（パーティ取得-予測を開始-パーティ保存の順）
- **ボタン:**
    - ID: `recognize-opponent-party-btn`
    - ラベル: `<i class="bi bi-camera-video"></i> パーティ取得`
    - スタイル: `btn btn-sm btn-info neon-border`
- **動作:**
    - 「解析を開始」ボタンが押され、解析中の状態でのみ活性化（クリック可能）となる。
    - 解析が停止している状態では非活性（disabled）とする。

### 2.2. ユーザーフロー

1. ユーザーが「解析を開始」ボタンを押し、リアルタイム解析を開始する。
2. 対戦相手の選出画面が表示される。
3. ユーザーが「パーティ取得」ボタンを押す。
4. ボタンにスピナーが表示され、処理中であることを示す。
5. 処理が完了すると、相手パーティ欄の6つの入力ボックスに、認識されたポケモン名が自動的に入力される。
6. 認識に失敗したスロットは空欄のままとなる。
7. 処理完了後、スピナーは消える。

## 3. フロントエンド設計 (JavaScript)

### 3.1. イベントリスナー

- `recognize-opponent-party-btn` のクリックイベントを捕捉する。
- クリック時、`toggle-analysis-button` の状態をチェックし、解析中でなければ処理を中断する。

### 3.2. API通信

- バックエンドの新規APIエンドポイント `/api/party/recognize_opponent` に対して、`POST`リクエストを送信する。
- リクエストボディは不要。
- レスポンスとして、認識されたポケモン名の配列（6要素）をJSON形式で受け取る。

### 3.3. DOM操作

- APIからレスポンスを受け取ったら、`opponent-party-display` 内の6つの `input` 要素を取得する。
- 受け取ったポケモン名の配列を元に、各 `input` 要素の `value` を設定する。

```javascript
// 疑似コード: main.js または関連モジュール内
const recognizeBtn = document.getElementById('recognize-opponent-party-btn');
const opponentInputs = document.querySelectorAll('#opponent-party-display .pokemon-input');

recognizeBtn.addEventListener('click', async () => {
    // ボタンを処理中状態にする
    setButtonLoading(recognizeBtn, true);

    try {
        const response = await fetch('/api/party/recognize_opponent', { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            data.party.forEach((pokemonName, index) => {
                if (opponentInputs[index]) {
                    opponentInputs[index].value = pokemonName;
                }
            });
            // 必要に応じて成功通知
        } else {
            // エラー通知
            console.error('パーティ認識失敗:', data.error);
        }
    } catch (error) {
        console.error('API通信エラー:', error);
    } finally {
        // ボタンの処理中状態を解除
        setButtonLoading(recognizeBtn, false);
    }
});
```

## 4. バックエンド設計 (Python/Flask)

### 4.1. APIエンドポイント

- **URL:** `/api/party/recognize_opponent`
- **Method:** `POST`
- **リクエスト:** なし
- **レスポンス (成功):**
  ```json
  {
    "success": true,
    "party": ["カイリュー", "ハバタクカミ", "パオジアン", "サーフゴー", "", "イーユイ"]
  }
  ```
  *(認識失敗した箇所は空文字)*
- **レスポンス (失敗):**
  ```json
  {
    "success": false,
    "error": "リアルタイム解析が実行されていません。"
  }
  ```

### 4.2. 処理フロー

1. APIリクエストを受け取る。
2. 現在のリアルタイム解析（キャプチャ）が実行中かを確認。実行中でなければエラーを返す。
3. 実行中のキャプチャスレッドから、最新のフレーム画像を取得する。
4. `instance/roi_config.json` を読み込み、`your_poke1` から `your_poke6` までのROI座標を取得する。
5. 6つのROI座標に基づき、最新フレームから6枚のポケモン画像を切り出す。
6. 各画像に対し、「5. ポケモン名判別ロジック」を実行する。
7. 判別結果（6体のポケモン名のリスト）を生成する。
8. 成功レスポンスとして、ポケモン名のリストをJSONで返す。

## 5. ポケモン名判別ロジック (テンプレートマッチング)

選出画面のポケモンはアイコン画像であるため、OCRよりもテンプレートマッチングが適している。

- **使用ライブラリ:** OpenCV (`cv2`)
- **テンプレート画像:** `data/pokemon_images/` 内の各ポケモンのアイコン画像。
- **処理手順:**
    1. **テンプレートの事前ロード:** サーバー起動時に、`data/pokemon_images/` 内のすべてのポケモン画像をグレースケールで読み込み、辞書（`{pokemon_name: image_data}`）としてメモリに保持する。
    2. **入力画像の前処理:** ROIから切り出した画像もグレースケールに変換する。
    3. **マッチング実行:**
        - 切り出した画像（入力画像）に対し、メモリ上のすべてのテンプレート画像との間で `cv2.matchTemplate` を実行する。
        - 類似度計算手法は `cv2.TM_CCOEFF_NORMED` （正規化相関係数）を推奨。
    4. **最良マッチの特定:**
        - `cv2.minMaxLoc` を使用して、最も類似度の高いテンプレート画像とその類似度スコアを取得する。
    5. **閾値判定:**
        - 取得した最高の類似度スコアが、あらかじめ設定した閾値（例: `0.8`）以上であれば、そのテンプレートのポケモン名を採用する。
        - 閾値に満たない場合は、認識失敗とし、空文字を返す。
    6. 上記2〜5を6枚の画像すべてに対して実行する。

## 6. 備考

- テンプレートマッチングの精度は、テンプレート画像の品質と、ゲーム画面の解像度に依存する。
- 将来的に新しいポケモンが追加された場合は、`data/pokemon_images/` にテンプレート画像を追加することで対応可能。


 ### 1. 格納するデータ


   - ポケモンのアイコン画像
   - ベースディレクトリ: C:\pokemon-ai-tool\data\pokemon_images\
  例えば、「カイリュー」と「サーフゴー」の2体を登録する場合、以下のようなフォルダ構成になります。


  `
  C:\pokemon-ai-tool\
  └── data\
      └── pokemon_images\
          ├── カイリュー\
          │   └── icon.png  (カイリューのアイコン画像)
          │
          ├── サーフゴー\
          │   └── icon.png  (サーフゴーのアイコン画像)
          │
          └── ... (他のポケモンのフォルダも同様に作成)
  `

  【重要】
  - フォルダ名は、プログラムが認識する際のポケモンの正式名称と一致させる必要があります。
  - 各ポケモンフォルダ内の画像ファイル名は自由ですが（例: カイリュー.png, 
  icon.jpgなど）、1つのフォルダに複数の画像がある場合は、最初に見つかったファイルがテンプレートとして使用されます。管理のしやすさから、icon.pngのような名前に統一することをお勧めします。


  この構造に従って画像を追加・整理することで、サーバー起動時にプログラムが自動でテンプレート画像を読み込み、認識対象として利用できるようになります。

下記を実行して大まかに準備
C:\pokemon-ai-tool\scripts\setup_template_images.py