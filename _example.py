import csv
from flask import Flask
from src.database.manager import db
from src.models.pokemon_model import PokemonModel
from src.models.move_model import MoveModel
from src.models.trained_pokemon_moedl import TrainedPokemonModel
from src.models.party_model import PartyModel
from src.models.partyMember_model import PartyMemberModel
from src.models.battle_model import BattleModel  # ORM層
from src.models.raw_battle_event_model import RawBattleEventModel

from src.schemas.pokemon_battle.battle_state import BattleState
from src.schemas.pokemon_battle.battle_side import BattleSide
from src.schemas.pokemon_battle.battle_field import BattleField
from src.schemas.pokemon_battle.pokemon import Pokemon
from src.schemas.pokemon_battle.move import Move
from src.schemas.pokemon_battle.party import Party
from src.schemas.pokemon_battle.battle_log import BattleLog  # スキーマ層

from src.services.calculate_service import DamageCalculator
from src.services.battle_state_builder_service import BattleStateBuilder
from src.services.battle_state_updater_service import BattleStateUpdater

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///C:/pokemon-ai-tool/data/pokemon_ai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)



def insert_raw_battle_events_from_csv(csv_path: str, battle_id: str) -> None:
    """
    CSVファイルからRawBattleEventを読み込み、DBに挿入する。
    CSV列: roi_name, frame_idx, ocr_text
    """
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if not {"roi_name", "frame_idx", "ocr_text"}.issubset(reader.fieldnames):
            raise ValueError("CSVに必要な列がありません（roi_name, frame_idx, ocr_text）")

        count_inserted = 0
        count_skipped = 0

        for row in reader:
            roi_name = row["roi_name"].strip()
            frame_idx = int(row["frame_idx"])
            ocr_text = row.get("ocr_text", "")

            # 重複チェック（UNIQUE(battle_id, sequence, roi_name)）
            existing = RawBattleEventModel.query.filter_by(
                battle_id=battle_id,
                sequence=frame_idx,
                roi_name=roi_name
            ).first()

            if existing:
                count_skipped += 1
                continue

            event = RawBattleEventModel(
                battle_id=battle_id,
                sequence=frame_idx,
                roi_name=roi_name,
                ocr_text=ocr_text,
            )

            db.session.add(event)
            count_inserted += 1

        db.session.commit()
        print(f"{count_inserted} 件挿入, {count_skipped} 件スキップ（既存データ）")



with app.app_context():
    # ------------------------
    # ログデータ投入テスト
    # ------------------------
    # csv_path = r"C:\pokemon-ai-tool\.prompt\battle_logs.csv"
    # battle_id = "BATTLE-20251018-0002"
    # insert_raw_battle_events_from_csv(csv_path, battle_id)


    # ------------------------
    # models,schemas取得テスト
    # ------------------------
    # PokemonModel
    # pokemon = PokemonModel.query.filter_by(name_ja="ピカチュウ").first()
    # pikachu = Pokemon.from_pokemon_model(pokemon, level=50)
    # print(pikachu.to_dict() if pokemon else "No record found")

    # MoveModel
    # move_model = MoveModel.query.filter_by(id=1).first()
    # move = Move.from_model(move_model)
    # print(move.to_dict() if move else "No record found")

    # ------------------------
    # pokemon ,パーティ取得
    # ------------------------
    # DBから読み込み
    # attacker_loaded_party = Party.load_from_db(2)
    # print(loaded_party.to_dict())

    # party_model = PartyModel.query.filter_by(id=2).first()
    # move = Move.from_model(party_model)
    # print(party_model.to_dict())

    # attacker_pokemon = TrainedPokemonModel.query.filter_by(id=9).first()
    # defender_pokemon = TrainedPokemonModel.query.filter_by(id=11).first()
    # battle_pokemon = Pokemon.from_trained_model(trained_pokemon)
    # print(battle_pokemon.to_dict() if battle_pokemon else "No record found")

    # ------------------------
    # battlestate取得
    # ------------------------
    # battlefield = BattleField()

    # my_loaded_party = Party.load_from_db(2)
    # my_side = BattleSide(team_name="attacker", pokemon_list=my_loaded_party.members)
    # my_active = my_side.team[0]
    # my_side.set_active(my_active)
    # move = my_active.moves[1]

    # opponent_loaded_party = Party.load_from_db(6)
    # opponent_loaded_party = []
    # opponent_loaded_party.append(Pokemon.from_pokemon_model(PokemonModel.query.filter_by(name_ja="ウルガモス").first(), level=50))
    # opponent_loaded_party.append(Pokemon.from_pokemon_model(PokemonModel.query.filter_by(name_ja="トドロクツキ").first(), level=50))
    # opponent_loaded_party.append(Pokemon.from_pokemon_model(PokemonModel.query.filter_by(name_ja="コライドン").first(), level=50))
    # opponent_loaded_party.append(Pokemon.from_pokemon_model(PokemonModel.query.filter_by(name_ja="タケルライコ").first(), level=50))
    # opponent_loaded_party.append(Pokemon.from_pokemon_model(PokemonModel.query.filter_by(name_ja="バシャーモ").first(), level=50))
    # opponent_loaded_party.append(Pokemon.from_pokemon_model(PokemonModel.query.filter_by(name_ja="ホウオウ").first(), level=50))


    # opponent_side = BattleSide(team_name="defender", pokemon_list=opponent_loaded_party)
    # opponent_active = opponent_side.team[2]
    # opponent_side.set_active(opponent_active)
    
    # battle_state = BattleState(side1=my_side, side2=opponent_side, field=battlefield, is_side1_attacker=True)

    # print(my_active.name)
    # print(opponent_active.name)
    # print(move.name)
    # ------------------------
    # ログ→対戦状況取得
    # ------------------------

    # DBからバトルログをロード
    battle_log = BattleLog.load_from_db("BATTLE-20251018-0002")
    
    # 1️⃣ バトルログをDBから取得
    battle_state = BattleStateBuilder.from_battle_log(battle_log)

    # 2️⃣ 初期BattleStateを構築
    state = BattleStateBuilder.from_battle_log(battle_log)


    # 3️⃣ フレーム単位でイベント適用
    calculator = DamageCalculator()
    updater = BattleStateUpdater(state, calculator)
    updater.apply_frames(battle_log.events)

    # ------------------------
    # ダメージ計算
    # ------------------------
    # デフォルト設定で計算機を作成
    # calculator = DamageCalculator()

    # ダメージ計算
    # min_damage, max_damage = calculator.calculate_damage(move, battle_state)
    # print(f"ダメージ: {min_damage} - {max_damage}")
    # # results = calculator.simulate_team_damage(battle_state)
    # estimate_ev_from_damage = calculator.estimate_ev_from_damage(
    #     move=move,
    #     battle_state=battle_state,
    #     observed_damage=(90, 100),
    #     target="attacker"
    # )

    # print(estimate_ev_from_damage["estimated_ev"])
    # print(estimate_ev_from_damage["range"])
    # print(estimate_ev_from_damage["num_candidates"])
    # print(estimate_ev_from_damage["detail"])
    
    # ------------------------
    # 
    # ------------------------