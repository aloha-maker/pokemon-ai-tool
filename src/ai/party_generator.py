import random

class PartyGenerator:
    """
    ユーザーの入力に基づき、パーティと運用ガイドを生成するクラス。
    """
    def generate(self, available_pokemon: list, concept: str):
        """
        パーティと運用ガイドを生成するメインメソッド。
        
        Args:
            available_pokemon (list): ユーザーが使用可能なポケモンのリスト。
            concept (str): ユーザーが希望する戦術コンセプト。

        Returns:
            dict: 生成されたパーティと運用ガイドを含む辞書。
        """
        # --- ここにAIのロジックを実装 ---
        # プロトタイプとして、利用可能ポケモンからランダムに6体選出するダミーロジック
        if len(available_pokemon) < 6:
            return {"error": "使用可能なポケモンが6体未満です。"}
        
        generated_party = random.sample(available_pokemon, 6)
        
        # ダミーの技構成や持ち物を付与
        party_details = []
        for name in generated_party:
            party_details.append({
                "name": name,
                "item": "いのちのたま",
                "ability": "いかく",
                "terastal_type": "ノーマル",
                "moves": ["10まんボルト", "れいとうビーム", "かえんほうしゃ", "まもる"]
            })
            
        # コンセプトに基づいたダミーの運用ガイドを生成
        manual = f"### {concept} 構築 運用ガイド\n\n"
        manual += f"この構築は「{concept}」をコンセプトとしています。\n"
        manual += f"**基本選出**: {party_details[0]['name']} + {party_details[1]['name']} + {party_details[2]['name']}\n"
        manual += "**立ち回り**: 初手に高火力のポケモンを出し、相手のサイクルに負荷をかけていくのが基本戦術です..."

        return {
            "party": party_details,
            "manual": manual
        }

