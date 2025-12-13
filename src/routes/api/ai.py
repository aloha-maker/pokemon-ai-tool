# src/routes/api/ai.py
import logging
from flask import Blueprint, request
from src.services.ai_service import AiService
from src.services.calculate_service import DamageCalculator
from src.ai.predictor import ActionAIModel
from src.utils.response_handler import api_success, api_fail, api_error

from src.schemas.pokemon_battle.battle_state import BattleState

ai_bp = Blueprint('ai_api', __name__, url_prefix='/api/ai')

@ai_bp.route('/predict', methods=['POST'])
def predict():
    """選出予測API"""
    service = AiService()
    data = request.json
    try:
        result = service.predict_best_team(
            my_party=data.get('my_party'),
            opponent_party=data.get('opponent_party')
        )
        return api_success(result)
    except ValueError as e:
        return api_fail({"error": str(e)})
    except Exception as e:
        logging.exception(e)
        return api_error("An internal server error occurred")

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
        return api_success(result)
    except ValueError as e:
        return api_fail({"error": str(e)})
    except Exception as e:
        logging.exception(e)
        return api_error("An internal server error occurred")

@ai_bp.route('/get_suggestion', methods=['POST'])
def get_suggestion():
    data = request.json
    battle_state = BattleState.from_dict(data)

    results = {}

    # 攻撃側のアクティブポケモンが持つ全技について、相手チーム全員に対するダメージをシミュレーションする。
    damage_calculator = DamageCalculator()
    damage_calcs = damage_calculator.simulate_team_damage(battle_state)
    results['damage_calcs'] = {'my_to_opponent' : damage_calcs,
        'opponent_to_my' : {}
        }


    # AIモデルで行動を予測　TODO
    # model = ActionAIModel(app_state=current_app.state)
    # recommendation = model.predict_action(battle_state)
    # del model # DB接続を閉じる

    best_move = "はかいこうせん"
    max_effectiveness = 100
    recommendation = {
            "action": "技選択",
            "target": best_move,
            "reason": f"最もダメージが期待できる技は「{best_move}」です (倍率: x{max_effectiveness})。"
        }
    results['recommendation'] = recommendation
    return results