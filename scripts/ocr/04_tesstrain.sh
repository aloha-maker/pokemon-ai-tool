#!/bin/bash

# 日付の取得（yyyymmdd形式）
TODAY=$(date +"%Y%m%d")

echo "=== Tesseract トレーニング処理を開始します ==="

# 1. 既存のground-truthフォルダをリネーム
echo "--- ステップ1: 既存のground-truthフォルダをリネーム ---"
if [ -d "/c/workspace/tesstrain/data/jpn_pokemon-ground-truth" ]; then
    mv "/c/workspace/tesstrain/data/jpn_pokemon-ground-truth" "/c/workspace/tesstrain/data/jpn_pokemon-ground-truth_${TODAY}"
    echo "リネーム成功: jpn_pokemon-ground-truth → jpn_pokemon-ground-truth_${TODAY}"
else
    echo "警告: ディレクトリ '/c/workspace/tesstrain/data/jpn_pokemon-ground-truth' が見つかりません"
fi

# 2. 新しいトレーニングデータを移動
echo "--- ステップ2: 新しいトレーニングデータを移動 ---"
if [ -d "/c/pokemon-ai-tool/.traindata/jpn_pokemon-ground-truth" ]; then
    mkdir -p "/c/workspace/tesstrain/data/jpn_pokemon-ground-truth"
    mv "/c/pokemon-ai-tool/.traindata/jpn_pokemon-ground-truth"/* "/c/workspace/tesstrain/data/jpn_pokemon-ground-truth/"
    echo "移動成功: /c/pokemon-ai-tool/.traindata/jpn_pokemon-ground-truth → /c/workspace/tesstrain/data/jpn_pokemon-ground-truth"
else
    echo "エラー: ディレクトリ '/c/pokemon-ai-tool/.traindata/jpn_pokemon-ground-truth' が見つかりません"
    exit 1
fi

# 3. 既存のモデルファイルをコピーしてリネーム
echo "--- ステップ3: 既存モデルファイルのコピー ---"
if [ -f "/c/pokemon-ai-tool/tessdata_custom/jpn_pokemon.traineddata" ]; then
    mkdir -p "/c/workspace/tesstrain/tessdata"
    cp "/c/pokemon-ai-tool/tessdata_custom/jpn_pokemon.traineddata" "/c/workspace/tesstrain/tessdata/jpn_pokemon_old.traineddata"
    echo "コピー成功: jpn_pokemon.traineddata → jpn_pokemon_old.traineddata"
else
    echo "警告: ファイル '/c/pokemon-ai-tool/tessdata_custom/jpn_pokemon.traineddata' が見つかりません"
fi

# 4. 既存の出力フォルダをリネーム
echo "--- ステップ4: 既存の出力フォルダをリネーム ---"
if [ -d "/c/workspace/tesstrain/data/jpn_pokemon" ]; then
    mv "/c/workspace/tesstrain/data/jpn_pokemon" "/c/workspace/tesstrain/data/jpn_pokemon_${TODAY}"
    echo "リネーム成功: jpn_pokemon → jpn_pokemon_${TODAY}"
else
    echo "情報: ディレクトリ '/c/workspace/tesstrain/data/jpn_pokemon' は存在しないためスキップ"
fi

# 5. フォルダ移動してトレーニング実行
echo "--- ステップ5: Tesseract トレーニングの実行 ---"
cd /c/workspace/tesstrain

# 既存モデルからの転移学習
make training MODEL_NAME=jpn_pokemon START_MODEL=jpn_pokemon_old TESSDATA=/c/workspace/tesstrain/tessdata

# 6. 生成されたトレーニングデータをコピー
echo "--- ステップ6: 新規トレーニングデータのコピー ---"
if [ -f "/c/workspace/tesstrain/data/jpn_pokemon.traineddata" ]; then
    mkdir -p "/c/pokemon-ai-tool/tessdata_custom"
    cp "/c/workspace/tesstrain/data/jpn_pokemon.traineddata" "/c/pokemon-ai-tool/tessdata_custom/"
    echo "コピー成功: /c/workspace/tesstrain/data/jpn_pokemon.traineddata → /c/pokemon-ai-tool/tessdata_custom/"
else
    echo "エラー: ファイル '/c/workspace/tesstrain/data/jpn_pokemon.traineddata' が見つかりません"
    exit 1
fi

# 7. 古いトレーニングデータファイルをリネーム
echo "--- ステップ7: 古いトレーニングデータファイルのリネーム ---"
if [ -f "/c/workspace/tesstrain/tessdata/jpn_pokemon_old.traineddata" ]; then
    mv "/c/workspace/tesstrain/tessdata/jpn_pokemon_old.traineddata" "/c/workspace/tesstrain/tessdata/jpn_pokemon_old_${TODAY}.traineddata"
    echo "リネーム成功: jpn_pokemon_old.traineddata → jpn_pokemon_old_${TODAY}.traineddata"
else
    echo "警告: ファイル '/c/workspace/tesstrain/tessdata/jpn_pokemon_old.traineddata' が見つかりません"
fi

echo "=== すべての処理が完了しました ==="