# src/services/trained_pokemon_service.py
from typing import List, Dict, Any
from src.extensions import db

from src.schemas.pokemon_battle import Pokemon
from src.models import TrainedPokemonModel,NatureModel,TypeModel,ItemModel,AbilityModel

class TrainedPokemonService:
    """育成済みポケモンに関するビジネスロジックを担当する"""    
    def get_by_id(self, pokemon_id: int) -> Dict[str, Any] | None:
        """IDで単一の育成済みポケモンを取得する"""
        trained_pokemon = TrainedPokemonModel.query.get(pokemon_id)
        if not trained_pokemon:
            return None
        return Pokemon.from_trained_model(trained_pokemon).to_dict()

    def get_all(self) -> List[Dict[str, Any]]:
        trained_pokemon_list = TrainedPokemonModel.query.all()
        return [Pokemon.from_trained_model(model).to_dict() for model in trained_pokemon_list]   

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

    def update(self, pokemon_id: int, data: Dict[str, Any]) -> bool:
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

    def delete(self, pokemon_id: int) -> bool:
        """育成済みポケモンを削除する"""
        try:
            model = TrainedPokemonModel.query.get(pokemon_id)
            if model:
                db.session.delete(model)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            raise e
