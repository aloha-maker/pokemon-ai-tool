# F-06 詳細設計書: OCR機能

## 1. 概要

本機能は、画面キャプチャ機能から受け取った画像データに対し、光学文字認識（OCR）を実行し、ゲーム内のテキスト情報（ポケモン名、HP、技リストなど）を抽出・構造化することを目的とする。

## 2. 責任範囲

- `roi_config.json` ファイルから、テキスト抽出対象領域（ROI）を読み込む。
- 基準解像度と実行時の画像解像度に基づき、ROI座標を動的にスケーリングする。
- OCRの認識精度を向上させるため、入力画像に対して前処理（グレースケール化、二値化など）を適用する。
- 前処理済みの画像領域に対し、`pytesseract` を用いてOCRを実行し、テキストを抽出する。
- 抽出したテキストを整形し、キーと値を対応付けた辞書形式のゲーム状態（`game_state`）として返す。

## 3. 主要コンポーネント

### 3.1. `GameStateParser` クラス (`src/core/ocr.py`)

画像フレームからゲーム状態を解析する処理全体をカプセル化するクラス。

#### 主要メソッド

- **`__init__(self, roi_config_path='roi_config.json')`**
  - **機能:** `GameStateParser` のインスタンスを初期化する。
  - **処理:**
    1. `_load_rois()` を呼び出し、ROI設定ファイルから「基準解像度」と「ROI辞書」を読み込み、それぞれインスタンス変数に保存する。

- **`_load_rois(self, path: str) -> tuple[dict | None, dict]`**
  - **機能:** ROI設定ファイル（JSON）を読み込む。
  - **戻り値:** `(基準解像度の辞書, ROIの辞書)` のタプル。
  - **処理:**
    1. JSONファイルを読み込む。
    2. `reference_resolution` キーが存在すれば、その値を基準解像度として分離する。
    3. 残りのキーと値をROI辞書として返す。
    4. ファイルが存在しない、またはパースに失敗した場合は `(None, {})` を返す。

- **`_scale_roi(self, roi: tuple, scale_w: float, scale_h: float) -> tuple`**
  - **機能:** 元のROI座標を、現在のフレームサイズに合わせてスケーリングする。
  - **引数:**
    - `roi` (tuple): `(x, y, w, h)` 形式のROI座標。
    - `scale_w` (float): 幅方向のスケーリング係数。
    - `scale_h` (float): 高さ方向のスケーリング係数。
  - **戻り値:** スケーリング後の新しいROI座標 `(x, y, w, h)`。

- **`_preprocess_image_for_ocr(self, img: np.ndarray) -> np.ndarray`**
  - **機能:** OCRの精度を向上させるための画像前処理を行う。
  - **処理:**
    1. `cv2.cvtColor` を用いて画像をグレースケールに変換する。
    2. `cv2.adaptiveThreshold` を用いて画像を二値化し、文字と背景を明確に分離する。

- **`parse_frame(self, frame: np.ndarray) -> dict`**
  - **機能:** 単一の画像フレームを解析し、構造化されたゲーム状態を返す。
  - **引数:** `frame` (np.ndarray): キャプチャされた画像フレーム。
  - **戻り値:** 抽出されたテキスト情報を含む辞書 (例: `{'my_pokemon_name': 'ピカチュウ', ...}`)
  - **処理:**
    1. `reference_resolution` と現在の `frame` のサイズから、スケーリング係数（`scale_w`, `scale_h`）を計算する。
    2. `self.rois` の各ROIに対してループ処理を行う。
    3. `_scale_roi()` を使ってROI座標をスケーリングする。
    4. スケーリング後の座標を使って、`frame` から対象領域の画像を切り抜く (`cropped_img`)。
    5. `_preprocess_image_for_ocr()` を使って切り抜いた画像を前処理する。
    6. `pytesseract.image_to_string()` を使って前処理済み画像からテキストを抽出する。
    7. 抽出したテキストをキーと共に `game_state` 辞書に格納する。
    8. 全てのROI処理後、`game_state` 辞書を返す。

## 4. データフロー

1. **入力:**
   - `BGR` 形式の画像データ (`numpy.ndarray`)
   - `roi_config.json` ファイル

2. **処理:**
   - `GameStateParser` がROI設定を読み込む。
   - `parse_frame` が呼ばれると、入力画像とROI設定に基づき、各領域の画像を切り出し、前処理、OCRを実行する。

3. **出力:**
   - ゲーム状態を表す辞書 (`dict`)

## 5. 依存関係

- **外部ライブラリ:**
  - `OpenCV` (`cv2`): 画像の前処理（グレースケール化、二値化など）。
  - `pytesseract`: Tesseract-OCRエンジンをPythonから利用するためのラッパー。
  - `NumPy`: 画像データの配列操作。
  - `Tesseract-OCR`: （外部アプリケーションとしてインストールが必要）

- **内部モジュール:**
  - なし

## 6. 設定ファイル

- **`roi_config.json`**
  - **役割:** OCRを実行する対象領域（ROI）の座標と、その座標の基準となった画面解像度を定義する。
  - **構造:**
    ```json
    {
      "reference_resolution": {
        "width": 2560,
        "height": 1440
      },
      "my_pokemon_name": [x, y, w, h],
      "opponent_pokemon_name": [x, y, w, h],
      ...
    }
    ```
