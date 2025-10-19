import pprint
from src.ai.win_rate_predictor import WinRatePredictor

def main():
    # --- テスト用のパーティデータ ---
    my_party = ["charizard", "blastoise", "venusaur", "pikachu", "snorlax", "gengar"]
    opponent_party = ["arcanine", "gyarados", "exeggutor", "alakazam", "machamp", "golem"]

    print("--- 選出予測シミュレーション ---")
    print(f"自パーティ: {', '.join(my_party)}")
    print(f"相手パーティ: {', '.join(opponent_party)}")
    print("--------------------------------")

    predictor = WinRatePredictor()
    recommendation = predictor.predict_best_team(my_party, opponent_party)
    
    print("\n【予測結果】")
    pprint.pprint(recommendation)

if __name__ == "__main__":
    main()