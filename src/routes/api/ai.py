# src/routes/api/ai.py
import logging
from flask import Blueprint, request, jsonify
from src.services.ai_service import AiService

ai_bp = Blueprint('ai_api', __name__, url_prefix='/api/ai')

@ai_bp.route('/predict', methods=['POST'])
def predict():
    """選出予測API"""
    service = AiService()
    data = request.json
    try:
        result = service.predict_best_team(
            my_party=data.get('my_party'),
            my_party_id=data.get('my_party_id'),
            opponent_party=data.get('opponent_party')
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception(e)
        return jsonify({"error": "An internal server error occurred"}), 500

@ai_bp.route('/generate-party', methods=['POST'])
def generate_party():
    """パーティ生成API"""
    service = AiService()
    data = request.json
    try:
        result = service.generate_party(
            available_pokemon=data.get('available_pokemon', []),
            concept=data.get('concept', '')
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception(e)
        return jsonify({"error": "An internal server error occurred"}), 500