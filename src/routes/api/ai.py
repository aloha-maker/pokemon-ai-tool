# src/routes/api/ai.py
from flask import Blueprint, request, jsonify
from src.ai.party_generator import PartyGenerator
from src.ai.win_rate_predictor import WinRatePredictor
from src.database.manager import DatabaseManager

ai_bp = Blueprint('ai_api', __name__, url_prefix='/api/ai')

@ai_bp.route('/predict', methods=['POST'])
def predict():
    data = request.json
    my_party_id = data.get('my_party_id')
    opponent_party = data.get('opponent_party', [])

    if my_party_id:
        with DatabaseManager() as db:
            my_party = db.get_party_pokemon_names(my_party_id)
    else:
        my_party = data.get('my_party', [])

    if len(my_party) != 6 or len(opponent_party) != 6:
        return jsonify({"error": "パーティはそれぞれ6体入力してください。"}), 400

    predictor = WinRatePredictor()
    result = predictor.predict_best_team(my_party, opponent_party)
    del predictor

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)

@ai_bp.route('/generate-party', methods=['POST'])
def generate_party():
    data = request.json
    available_pokemon = data.get('available_pokemon', [])
    concept = data.get('concept', '')

    if not available_pokemon or not concept:
        return jsonify({"error": "使用可能なポケモンと戦術コンセプトを入力してください。"}), 400

    generator = PartyGenerator()
    result = generator.generate(available_pokemon, concept)

    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)
