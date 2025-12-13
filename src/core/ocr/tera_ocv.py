import cv2
import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

def identify_tera_from_cropped_image(cropped_image_path, icons_dir, threshold=0.8):
    """
    すでに切り取られたテラスタルアイコン画像が、どのテラスタルタイプに最も一致するかを判別する。

    Args:
        cropped_image_path (str): 判別対象となる、切り取り済みの画像パス。
        icons_dir (str): 比較用のテラスタルアイコン画像が格納されているフォルダのパス。
        threshold (float): 一致していると判断するための信頼度の閾値 (0.0から1.0)。

    Returns:
        str: 検出されたテラスタルタイプの日本語名（例: 'ノーマルテラスタル'）。
             閾値を超えるアイコンが見つからない場合は None を返す。
    """
    # --- 1. テラスタルタイプ名の翻訳データを読み込み ---
    tera_json_path = os.path.join(basedir, 'instance', 'type.json')
    try:
        with open(tera_json_path, 'r', encoding='utf-8') as f:
            tera_data = json.load(f)
        tera_mapping = {item['en']: item['ja'] for item in tera_data['タイプ名一覧']}
    except Exception as e:
        print(f"[エラー] テラスタルタイプデータの読み込みに失敗しました: {e}")
        return None
    
    # --- 2. 判別対象の画像とアイコンリストを準備 ---
    if not os.path.exists(cropped_image_path):
        print(f"[エラー] 判別対象の画像が見つかりません: {cropped_image_path}")
        return None
    
    # 判別対象の画像を読み込む
    target_image = cv2.imread(cropped_image_path)
    if target_image is None:
        print(f"[エラー] 画像の読み込みに失敗しました: {cropped_image_path}")
        return None

    # アイコンフォルダから判別候補のリストを取得
    try:
        tera_files = [f for f in os.listdir(icons_dir) if f.endswith('.jpg')]
        if not tera_files:
            print(f"[エラー] アイコンフォルダにPNG画像が見つかりません: {icons_dir}")
            return None
    except FileNotFoundError:
        print(f"[エラー] アイコンフォルダが見つかりません: {icons_dir}")
        return None

    # --- 3. 全てのアイコン候補と比較し、最も一致するものを探す ---
    best_match = {
        'name': None,
        'score': -1.0,  # マッチ度の初期値
    }

    # icons_dir 内の全ての .png ファイルに対してループ
    for filename in tera_files:
        tera_name = os.path.splitext(filename)[0]
        template_path = os.path.join(icons_dir, filename)

        template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        if template is None:
            # 読み込み失敗はスキップ
            continue
        
        # テンプレートのサイズが判別対象より大きい場合はスキップ
        if template.shape[0] > target_image.shape[0] or template.shape[1] > target_image.shape[1]:
            continue

        # テンプレートマッチング実行
        use_mask = template.shape[2] == 4
        if use_mask:
            template_bgr = template[:, :, :3]
            alpha_mask = template[:, :, 3]
            result = cv2.matchTemplate(target_image, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_mask)
        else:
            result = cv2.matchTemplate(target_image, template, cv2.TM_CCOEFF_NORMED)
        
        # 今回のマッチングの最大値を取得
        _, max_val, _, _ = cv2.minMaxLoc(result)

        # これまでの最高スコアを上回った場合、情報を更新
        if max_val > best_match['score']:
            best_match['name'] = tera_name
            best_match['score'] = max_val

    # --- 4. 最終的な判定と結果の返却 ---
    # 最もスコアが高かったものが、設定した閾値を超えているか確認
    if best_match['score'] >= threshold:
        # 英語名を日本語名に変換
        japanese_name = tera_mapping.get(best_match['name'], best_match['name'])
        # デバッグ用にログを出力
        print(f"[情報] 最も一致するテラスタルタイプ: '{japanese_name}' (信頼度: {best_match['score']:.2%})")
        return japanese_name
    else:
        print(f"[情報] 閾値を超えるテラスタルタイプは見つかりませんでした。(最高信頼度: {best_match['score']:.2%})")
        return None