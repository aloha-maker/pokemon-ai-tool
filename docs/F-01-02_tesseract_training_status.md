# Tesseract OCRモデル学習の進捗と残作業

## 概要

`F-01-02_tesseract_training_procedure.md` に基づく、ポケモン名特化OCRモデルの学習タスクに関する現在の進捗状況と、今後実施が必要な作業をまとめる。

## 現在の進捗状況

### ステップ1: フォント画像のデータセット準備 (完了)

`C:\pokemon-ai-tool\dataset` ディレクトリ内に、Tesseract学習用の画像ファイル (`jpn.pkmn.exp.[n].png`)、教師テキストファイル (`jpn.pkmn.exp.[n].gt.txt`)、およびボックスファイル (`jpn.pkmn.exp.[n].box`) が多数存在することを確認しました。これにより、データセットの準備は完了していると判断されます。

## 残りの作業

### 1. ステップ2: Tesseract学習環境の構築 (未完了)

Tesseractのモデル学習に必要なツールとライブラリを準備する。

#### 2.1. Tesseract本体のインストール

- **Windowsの場合:**
    1.  [Tesseract OCRの公式ダウンロードページ](https://tesseract-ocr.github.io/tessdoc/Downloads.html) から、Windows版インストーラー (`tesseract-ocr-w64-setup-vX.XX.exe` のようなファイル) をダウンロードし、実行する。
    2.  インストール時に「Additional language data」で `Japanese` を選択し、日本語学習済みデータ (`jpn.traineddata`) もインストールされるようにする。
    3.  インストール後、Tesseractの実行ファイル (`tesseract.exe` が存在するディレクトリ、`C:\Program Files\Tesseract-OCR`) をシステムの環境変数 `Path` に追加する。
    4.  コマンドプロンプトで `tesseract --version` を実行し、Tesseractが正しくインストールされ、パスが通っていることを確認する。

#### 2.2. 学習ツールの取得 (`tesstrain`)

Tesseractのモデル学習用のスクリプト群である `tesstrain` をGitHubからクローンする。

1.  コマンドプロンプトまたはGit Bashを開き、任意の作業ディレクトリに移動する。
2.  以下のコマンドを実行して `tesstrain` リポジトリをクローンする。
    ```bash
    git clone https://github.com/tesseract-ocr/tesstrain.git
    ```
3.  クローン後、`tesstrain` ディレクトリが作成されていることを確認する。

#### 2.3. 依存ライブラリのインストール

`tesstrain` の実行に必要な依存パッケージをインストールする。

- **Windowsの場合 (MinGW/MSYS2の導入):**
    Tesseractの学習ツールは `make` や `g++` などのUnix系ツールを必要とするため、MinGWやMSYS2のような環境を導入する必要がある。
    1.  [MSYS2の公式ウェブサイト](https://www.msys2.org/) からインストーラーをダウンロードし、指示に従ってインストールする。
    2.  MSYS2ターミナルを開き、以下のコマンドを実行して必要なパッケージをインストールする。
        ```bash
        pacman -Syu
        pacman -S make automake gcc pkg-config
        ```
    4.  Python製のヘルパースクリプト用に、`tesstrain` ディレクトリ内の `requirements.txt` があれば、それを使ってPythonライブラリをインストールする。
        ```bash
        pip install -r tesstrain/requirements.txt
        ```
        もし `requirements.txt` がない場合、`Pillow` や `numpy` など、画像処理に必要な一般的なライブラリをインストールする。
        ```bash
        pip install Pillow numpy
        ```

- **課題:**
    - 複雑な依存関係による環境構築の難しさ。特にWindows環境ではMinGW/MSYS2の導入が必要となり、設定が煩雑になる場合がある。

### 2. ステップ3: モデルの学習実行と適用 (未着手)

- **作業内容:**
    - `tesstrain` を使用してモデルの学習を実行する。
    - 生成された新しいモデルファイル (`.traineddata`) をTesseractの`tessdata`ディレクトリに配置する。
    - Pythonコード (`pytesseract`) で、新しく作成したモデルを指定してOCRを実行するよう変更する。
- **課題:**
    - 高いマシン負荷と長い学習時間。
    - 精度向上のためのパラメータ調整。
  
  tesstrainのREADME.mdに基づき、
  make training MODEL_NAME=jpn_pokemon START_MODEL=jpn
  コマンドを実行します。このコマンドはMSYS2ターミナルでC:\
  pokemon-ai-ai-tool\tesstrainディレクトリ内で実行する必要があります。学習には高いマシン負荷と時
  間がかかるため、完了後にお知らせください。



  ✦ jpn.traineddataが見つからないエラーは、tesstrainがTesseractのインストールディレクトリにある既
  存の日本語モデルファイルを見つけられないためです。
  tesstrainのMakefileにTESSDATA変数を設定し、jpn.traineddataのパスを教える必要があります。
  MSYS2ターミナルで
  make training MODEL_NAME=jpn_pokemon START_MODEL=jpn TESSDATA="/c/Program Files/Tesseract-OCR/tessdata"
  を実行してください。

  cd \c\pokemon-ai-tool\tesstrain
  make training MODEL_NAME=jpn_pokemon START_MODEL=jpn TESSDATA="/c/PROGRA~1/Tesseract-OCR/tessdata"



PATH="/c/Program Files/Tesseract-OCR:$PATH" 

make training MODEL_NAME=jpn_pokemon START_MODEL=jpn TESSDATA="/c/pokemon-ai-tool/tessdata_custom"

make training MODEL_NAME=jpn_pokemon START_MODEL=jpn TESSDATA="/c/pokemon-ai-tool/tessdata_custom"
」

/usr/bin/make training MODEL_NAME=jpn_pokemon START_MODEL=jpn TESSDATA="/c/pokemon-ai-tool/tessdata_custom"

    /usr/bin/make training MODEL_NAME=jpn_pokemon START_MODEL=jpn TESSDATA="/c/pokemon-ai-tool/tessdata_custom" GROUND_TRUTH_DIR="/c/pokemon-ai-tool/dataset"

/usr/bin/make training MODEL_NAME=jpn_pokemon START_MODEL=jpn TESSDATA="/c/pokemon-ai-tool/tessdata_custom" GROUND_TRUTH_DIR="/c/pokemon-ai-tool/dataset"