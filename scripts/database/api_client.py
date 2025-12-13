import requests
import time

def fetch_from_pokeapi(endpoint=None, resource_id=None, url=None, retries=3, backoff_factor=0.5):
    """PokeAPIからデータを取得する共通関数"""
    if url is None:
        url = f"https://pokeapi.co/api/v2/{endpoint}/{resource_id}"
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"\nURLの取得中にエラーが発生しました: {url} (試行 {i+1}/{retries}) - {e}")
            if i == retries - 1:
                print(f"URLの取得に失敗しました: {url}")
            time.sleep(backoff_factor * (2 ** i))
    return None

def get_all_resources(endpoint, limit=2000):
    """指定されたエンドポイントからすべてのリソースリストを取得する"""
    url = f"https://pokeapi.co/api/v2/{endpoint}?limit={limit}"
    data = fetch_from_pokeapi(url=url)
    return data.get('results', []) if data else []

def get_japanese_name(data):
    """データから日本語名を取得する"""
    # ja-Hrkt (ひらがな・カタカナ) を優先して探す
    for name_info in data.get('names', []):
        if name_info['language']['name'] == 'ja-Hrkt':
            return name_info['name']
    # 見つからない場合は ja (漢字) を探す
    for name_info in data.get('names', []):
        if name_info['language']['name'] == 'ja':
            return name_info['name']
    # 日本語名がなければ空文字を返す
    return ""
