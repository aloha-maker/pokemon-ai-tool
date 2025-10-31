from flask import Flask
from src.database.manager import db
from src.models.pokemon_model import PokemonModel
from src.models.move_model import MoveModel
from src.models.trained_pokemon_moedl import TrainedPokemonModel

from src.schemas.pokemon_battle.battle_state import BattleState
from src.schemas.pokemon_battle.battle_side import BattleSide
from src.schemas.pokemon_battle.battle_field import BattleField
from src.schemas.pokemon_battle.pokemon import Pokemon
from src.schemas.pokemon_battle.move import Move

from src.services.calculate_service import DamageCalculator

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///C:/pokemon-ai-tool/data/pokemon_ai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # pokemon = PokemonModel.query.filter_by(name_ja="ピカチュウ").first()
    # print(pokemon.to_dict() if pokemon else "No record found")

    # move_model = MoveModel.query.filter_by(id=1).first()
    # move = Move.from_model(move_model)
    # print(move.to_dict() if move else "No record found")


    attacker_pokemon = TrainedPokemonModel.query.filter_by(id=11).first()
    defender_pokemon = TrainedPokemonModel.query.filter_by(id=11).first()
    # battle_pokemon = Pokemon.from_trained_model(trained_pokemon)
    # print(battle_pokemon.to_dict() if battle_pokemon else "No record found")

    # デフォルト設定で計算機を作成
    calculator = DamageCalculator()

    battlefield = BattleField()

    attacker = Pokemon.from_trained_model(attacker_pokemon)
    print(attacker.to_dict())
    attacker_side = BattleSide(team_name="attacker", pokemon_list=[attacker])
    move = attacker.moves[0]

    
    defender = Pokemon.from_trained_model(defender_pokemon)
    defender_side = BattleSide(team_name="defender", pokemon_list=[defender])

    battle_state = BattleState(side1=attacker_side, side2=defender_side, field=battlefield, is_side1_attacker=True)

    # ダメージ計算
    min_damage, max_damage = calculator.calculate_damage(move, battle_state)
    print(f"ダメージ: {min_damage} - {max_damage}")