import cv2
import numpy as np
import os
from glob import glob

def test_ocv_accuracy():
    """
    画像を1件だけ読み取ってOCVの精度を確認するスクリプト
    """
    # 固定パスの設定
    TEST_IMAGE_PATH = r'C:\pokemon-ai-tool\.traindata\text2img\test_full\stay_text\130b9b4b_stay_text_001380.png'
    TEMPLATE_DIR = r'C:\pokemon-ai-tool\static\others'
    
    print("=" * 60)
    print("OCV精度テストスクリプト")
    print("=" * 60)
    
    # テスト画像の存在確認
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ テスト画像が見つかりません: {TEST_IMAGE_PATH}")
        print("以下のパスに画像があるか確認してください:")
        possible_dirs = glob(r'C:\pokemon-ai-tool\.traindata\text2img\*\stay_text\*.png')
        if possible_dirs:
            print("見つかった可能性のあるパス:")
            for path in possible_dirs[:5]:  # 最初の5件のみ表示
                print(f"  - {path}")
        return
    
    # テンプレートディレクトリの存在確認
    if not os.path.exists(TEMPLATE_DIR):
        print(f"❌ テンプレートディレクトリが見つかりません: {TEMPLATE_DIR}")
        return
    
    # テスト画像の読み込み
    test_image = cv2.imread(TEST_IMAGE_PATH)
    if test_image is None:
        print(f"❌ テスト画像の読み込みに失敗しました: {TEST_IMAGE_PATH}")
        return
    
    print(f"✅ テスト画像読み込み成功: {TEST_IMAGE_PATH}")
    print(f"   画像サイズ: {test_image.shape[1]}x{test_image.shape[0]}")
    
    # テンプレート画像の検索
    template_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        template_files.extend(glob(os.path.join(TEMPLATE_DIR, ext)))
    
    if not template_files:
        print(f"❌ テンプレート画像が見つかりません: {TEMPLATE_DIR}")
        return
    
    print(f"✅ テンプレート画像 {len(template_files)} 件見つかりました")
    
    # 各テンプレートとのマッチング実行
    results = []
    
    for template_path in template_files:
        template_name = os.path.basename(template_path)
        template = cv2.imread(template_path)
        
        if template is None:
            print(f"⚠ テンプレート読み込み失敗: {template_name}")
            continue
        
        # テンプレートサイズがテスト画像より大きい場合はスキップ
        if template.shape[0] > test_image.shape[0] or template.shape[1] > test_image.shape[1]:
            print(f"⚠ テンプレートサイズが大きすぎます: {template_name} ({template.shape[1]}x{template.shape[0]})")
            continue
        
        # テンプレートマッチング実行（複数手法）
        methods = [
            ('TM_CCOEFF', cv2.TM_CCOEFF, False),
            ('TM_CCOEFF_NORMED', cv2.TM_CCOEFF_NORMED, True),
            ('TM_CCORR', cv2.TM_CCORR, False),
            ('TM_CCORR_NORMED', cv2.TM_CCORR_NORMED, True),
            ('TM_SQDIFF', cv2.TM_SQDIFF, False),
            ('TM_SQDIFF_NORMED', cv2.TM_SQDIFF_NORMED, True)
        ]
        
        for method_name, method, is_normalized in methods:
            try:
                result = cv2.matchTemplate(test_image, template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # 手法によって最適値が異なる
                if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                    # 最小値が最適（0に近いほど良い）
                    score = 1 - min_val if is_normalized else -min_val
                    best_val = min_val
                    best_loc = min_loc
                    optimal_value = "最小値"
                else:
                    # 最大値が最適（1に近いほど良い）
                    score = max_val
                    best_val = max_val
                    best_loc = max_loc
                    optimal_value = "最大値"
                
                results.append({
                    'template': template_name,
                    'method': method_name,
                    'score': score,
                    'best_val': best_val,
                    'location': best_loc,
                    'template_size': template.shape[:2],
                    'is_normalized': is_normalized,
                    'optimal_value': optimal_value
                })
                
            except Exception as e:
                print(f"⚠ マッチングエラー ({method_name} - {template_name}): {e}")
    
    # 結果のソートと表示
    if not results:
        print("❌ 有効なマッチング結果がありませんでした")
        return
    
    # 正規化された手法のみを対象にスコアでソート（降順）
    normalized_results = [r for r in results if r['is_normalized']]
    normalized_results.sort(key=lambda x: x['score'], reverse=True)
    
    print("\n" + "=" * 60)
    print("正規化マッチング結果（全件）")
    print("=" * 60)
    
    for i, result in enumerate(normalized_results):
        status = "✅" if result['score'] >= 0.8 else "❌"
        print(f"{i+1:2d}. {status} {result['template']:20} | {result['method']:15} | スコア: {result['score']:.4f}")
        print(f"     詳細: {result['optimal_value']}={result['best_val']:.4f}, 位置={result['location']}, テンプレートサイズ={result['template_size']}")
    
    # 全手法の結果表示（参考用）
    print("\n" + "=" * 60)
    print("全マッチング手法の結果（参考）")
    print("=" * 60)
    
    for i, result in enumerate(results[:10]):  # 上位10件のみ表示
        normalized_mark = "🔸" if result['is_normalized'] else "  "
        print(f"{normalized_mark} {result['template']:20} | {result['method']:15} | スコア: {result['score']:12.2f}")
    
    # 最高スコアの結果を詳細表示（正規化手法の中から）
    if normalized_results:
        best_result = normalized_results[0]
        print("\n" + "=" * 60)
        print("最高スコアの詳細（正規化手法）")
        print("=" * 60)
        print(f"テンプレート: {best_result['template']}")
        print(f"手法: {best_result['method']}")
        print(f"スコア: {best_result['score']:.4f}")
        print(f"詳細値: {best_result['best_val']:.4f}")
        print(f"位置: {best_result['location']}")
        print(f"テンプレートサイズ: {best_result['template_size']}")
        print(f"最適値タイプ: {best_result['optimal_value']}")
        
        # 閾値による判定（正規化手法のみ有効）
        threshold = 0.8
        if best_result['score'] >= threshold:
            print(f"✅ 判定結果: マッチング成功 (閾値 {threshold} 以上)")
        else:
            print(f"❌ 判定結果: マッチング失敗 (閾値 {threshold} 未満)")
        
        # 可視化（オプション）
        visualize_results = input("\n可視化結果を表示しますか？ (y/n): ").lower().strip()
        if visualize_results == 'y':
            visualize_matching(test_image, best_result, TEMPLATE_DIR)
    else:
        print("❌ 正規化手法での有効な結果がありません")

def visualize_matching(test_image, best_result, template_dir):
    """
    マッチング結果を可視化
    """
    template_path = os.path.join(template_dir, best_result['template'])
    template = cv2.imread(template_path)
    
    if template is None:
        print(f"❌ テンプレート読み込み失敗: {template_path}")
        return
    
    # マッチング位置に矩形を描画
    result_image = test_image.copy()
    h, w = template.shape[:2]
    top_left = best_result['location']
    bottom_right = (top_left[0] + w, top_left[1] + h)
    
    # 矩形描画
    cv2.rectangle(result_image, top_left, bottom_right, (0, 255, 0), 2)
    
    # テキスト追加
    text = f"{best_result['template']} ({best_result['score']:.3f})"
    cv2.putText(result_image, text, (top_left[0], top_left[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # 画像表示
    cv2.imshow('マッチング結果', result_image)
    cv2.imshow('テンプレート', template)
    cv2.imshow('テスト画像', test_image)
    
    print("画像を表示中... 何かキーを押すと終了します")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def test_multiple_thresholds():
    """
    複数の閾値でテストを実行（正規化手法のみ）
    """
    print("\n" + "=" * 60)
    print("複数閾値テスト（正規化手法）")
    print("=" * 60)
    
    # 固定パスの設定
    TEST_IMAGE_PATH = r'C:\pokemon-ai-tool\.traindata\text2img\test_video\stay_text\abc123_stay_text_000000.png'
    TEMPLATE_PATH = r'C:\pokemon-ai-tool\static\others\stay_text.png'
    
    if not os.path.exists(TEST_IMAGE_PATH) or not os.path.exists(TEMPLATE_PATH):
        print("❌ テストファイルが見つかりません")
        return
    
    test_image = cv2.imread(TEST_IMAGE_PATH)
    template = cv2.imread(TEMPLATE_PATH)
    
    if test_image is None or template is None:
        print("❌ 画像読み込み失敗")
        return
    
    # 正規化手法のみテスト
    normalized_methods = [
        ('TM_CCOEFF_NORMED', cv2.TM_CCOEFF_NORMED),
        ('TM_CCORR_NORMED', cv2.TM_CCORR_NORMED),
        ('TM_SQDIFF_NORMED', cv2.TM_SQDIFF_NORMED)
    ]
    
    for method_name, method in normalized_methods:
        print(f"\n--- {method_name} ---")
        result = cv2.matchTemplate(test_image, template, method)
        
        if method in [cv2.TM_SQDIFF_NORMED]:
            # 最小値が最適
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            score = 1 - min_val
            print(f"一致度: {score:.4f} (最小値: {min_val:.4f})")
        else:
            # 最大値が最適
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            score = max_val
            print(f"一致度: {score:.4f} (最大値: {max_val:.4f})")
        
        print("閾値テスト結果:")
        thresholds = [0.9, 0.8, 0.7, 0.6, 0.5]
        for threshold in thresholds:
            if score >= threshold:
                print(f"  ✅ 閾値 {threshold}: 成功")
            else:
                print(f"  ❌ 閾値 {threshold}: 失敗")

def explain_matching_methods():
    """
    マッチング手法の説明
    """
    print("\n" + "=" * 60)
    print("マッチング手法の説明")
    print("=" * 60)
    print("🔸 TM_CCOEFF_NORMED: 正規化相関係数 (推奨)")
    print("   - 範囲: 0.0 〜 1.0")
    print("   - 1.0: 完全一致, 0.0: 不一致")
    print("   - 照明変化に強い")
    print()
    print("🔸 TM_CCORR_NORMED: 正規化相互相関")
    print("   - 範囲: 0.0 〜 1.0") 
    print("   - 1.0: 完全一致, 0.0: 不一致")
    print()
    print("🔸 TM_SQDIFF_NORMED: 正規化二乗差")
    print("   - 範囲: 0.0 〜 1.0")
    print("   - 0.0: 完全一致, 1.0: 不一致")
    print("   - 背景が暗い画像に適する")
    print()
    print("非正規化手法（参考）:")
    print("  TM_CCOEFF, TM_CCORR, TM_SQDIFF")
    print("  - 絶対値を返すためサイズ依存")
    print("  - 閾値設定が困難")

if __name__ == "__main__":
    test_ocv_accuracy()
    test_multiple_thresholds()
    explain_matching_methods()
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)