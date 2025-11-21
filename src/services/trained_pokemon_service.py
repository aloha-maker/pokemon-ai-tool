# src/services/trained_pokemon_service.py
from typing import List, Dict, Any
from src.extensions import db

from src.schemas.pokemon_battle import Pokemon

from src.models.trained_pokemon_moedl import TrainedPokemonModel
from src.models.natures_model import NatureModel
from src.models.type_model import TypeModel
from src.models.item_model import ItemModel
from src.models.abilities_model import AbilityModel

class TrainedPokemonService:
    """育成済みポケモンに関するビジネスロジックを担当する"""
    def get_by_id(self, pokemon_id: int) -> Dict[str, Any] | None:
        """IDで単一の育成済みポケモンを取得する"""
        trained_pokemon = TrainedPokemonModel.query.get(pokemon_id)
        pokemon = Pokemon.from_trained_model(trained_pokemon)
        return pokemon.to_dict()

    def get_all(self) -> List[Dict[str, Any]]:
        """すべての育成済みポケモンを取得する"""
        trainde_pokemon_list = []
        trainde_pokemon_model_list = TrainedPokemonModel.query.all()
        for trainde_pokemon_model in trainde_pokemon_model_list:
            trainde_pokemon = self.get_by_id(trainde_pokemon_model.id)
            trainde_pokemon_list.append(trainde_pokemon)
        print(trainde_pokemon_list)
        return trainde_pokemon_list    

    def create(self, data: Dict[str, Any]) -> int:
        """育成済みポケモンを新規追加する"""
        try:
            pokemon = TrainedPokemonModel(**data)

            db.session.add(pokemon)
            db.session.commit()

            return pokemon.id  # 作成したIDを返す

        except Exception as e:
            db.session.rollback()
            raise e

    def update(self, pokemon_id: int, data: Dict[str, Any]) -> int:
        """育成済みポケモンを更新する"""
        try:
            pokemon = TrainedPokemonModel.query.get(pokemon_id)
            if not pokemon:
                return False

            TrainedPokemonModel.query.filter_by(id=pokemon_id).update(data)
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self, id: int) -> int:
        """育成済みポケモンを削除する"""
        try:
            model = TrainedPokemonModel.query.get(id)
            print(model)
            if model:
                db.session.delete(model)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            raise e
