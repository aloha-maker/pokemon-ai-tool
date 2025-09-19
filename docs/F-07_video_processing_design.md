# F-07 詳細設計書: 動画解析機能

## 1. 概要

本機能は、ユーザーによってアップロードされた対戦動画ファイルを解析し、フレームごとの差分検出に基づいて重要なシーン（大きな変化があったシーン）を特定し、そのシーンの画像からOCRで情報を抽出することを目的とする。最終的に、一連のターン情報を構造化し、データベースに保存する。

## 2. 責任範囲

- アップロードされた動画ファイルをフレーム単位で読み込む。
- フレーム間の差分を計算し、差分が閾値を超えた「重要フレーム」を検出する。
- 検出した重要フレームに対し、`GameStateParser` (OCR機能) を使ってゲーム状態を抽出する。
- 抽出した一連のゲーム状態を、ターンごとのデータとして整理・構造化する。
- 解析結果を `DatabaseManager` に渡し、データベースへの保存を依頼する。

## 3. 主要コンポーネント

### 3.1. `VideoProcessor` クラス (`src/core/video_processor.py`)

動画解析のプロセス全体を管理するクラス。

#### 主要メソッド

- **`__init__(self, video_path: str)`**
  - **機能:** `VideoProcessor` のインスタンスを初期化する。
  - **引数:**
    - `video_path` (str): 解析対象の動画ファイルのパス。
  - **処理:**
    1. `video_path` をインスタンス変数に保存する。
    2. `GameStateParser` のインスタンスを生成・保存する。
    3. `cv2.VideoCapture` を使って動画ファイルを開く。

- **`analyze(self) -> dict`**
  - **機能:** 動画全体の解析を実行し、ターンごとのデータを抽出する。
  - **戻り値:** ターン情報を構造化した辞書。
  - **処理:**
    1. `_find_significant_changes()` を呼び出して、動画内の大きな変化点をすべて検出する。
    2. 検出された各変化点のフレームに対し、`GameStateParser.parse_frame()` を使ってOCRを実行し、ゲーム状態を抽出する。
    3. 抽出された一連のゲーム状態から、重複の削除や順序の整理を行い、一貫性のあるターン進行データを構築する（`_reconstruct_turns` が担当）。
    4. 最終的に構造化された対戦ログデータを返す。

- **`_find_significant_changes(self, threshold=1000000, interval=30) -> list[np.ndarray]`**
  - **機能:** フレーム間の差分を計算し、大きな変化があったフレームをリストとして返す。
  - **引数:**
    - `threshold` (int): 変化を「重要」と判断するための差分閾値。
    - `interval` (int): フレームを比較する間隔（フレーム数）。
  - **戻り値:** 重要な変化が検出されたフレーム画像のリスト。
  - **処理:**
    1. 動画を `interval` フレームごとに読み進める。
    2. 前のフレームとの間で `cv2.absdiff` を使って差分を計算する。
    3. 差分の合計値が `threshold` を超えた場合、そのフレームを「重要フレーム」とみなし、リストに追加する。

- **`_reconstruct_turns(self, ocr_results: list[dict]) -> dict`**
  - **機能:** OCR結果のリストから、重複を排除し、論理的なターン進行を再構築する。
  - **引数:** `ocr_results`: `parse_frame` から得られた辞書のリスト。
  - **戻り値:** ターンごとに整理されたデータの辞書。
  - **処理:** (※ `turn_reconstructor.py` に実装が移譲される可能性がある)
    1. 連続する同一のOCR結果をマージする。
    2. HPの変動、ポケモン名の変更などをトリガーに、ターンの区切りを判断する。
    3. ターン番号を付与し、各ターンで発生したイベントを時系列に整理する。

## 4. データフロー

1. **入力:**
   - 対戦動画ファイル (例: `.mp4`)

2. **処理:**
   - `app.py` の `/api/videos/upload` エンドポイントが動画ファイルを受け取り、バックグラウンドタスクとして `analyze_video_task` を起動する。
   - `analyze_video_task` が `VideoProcessor` をインスタンス化し、`analyze()` を呼び出す。
   - `VideoProcessor` が動画を解析し、OCR結果を `DatabaseManager` に渡す。

3. **出力:**
   - `DatabaseManager` を介して、`battle_logs` テーブルに登録されるレコード。
   - `app.py` の `video_tasks` 辞書にタスクの完了状態と結果（`log_id`）が保存される。

## 5. 依存関係

- **外部ライブラリ:**
  - `OpenCV` (`cv2`): 動画の読み込み、フレームの差分計算。

- **内部モジュール:**
  - `src.core.ocr.GameStateParser`: フレーム画像からテキスト情報を抽出するために利用。
  - `src.database.manager.DatabaseManager`: 解析結果をデータベースに保存するために利用。
  - `src.core.turn_reconstructor` (想定): OCR結果のシーケンスから論理的なターンを再構築するために利用。

## 6. APIエンドポイント (`app.py`)

- **`POST /api/videos/upload`**
  - 動画ファイルを受け取り、解析タスクを開始する。
- **`GET /api/videos/status/<task_id>`**
  - 指定されたタスクの進捗状況（PENDING, PROCESSING, DONE, ERROR）を返す。
- **`GET /api/videos/result/<log_id>`**
  - 完了したタスクの解析結果をデータベースから取得して返す。
