# src/services/master_data_service.py
from src.models import ItemModel,NatureModel,AbilityModel,MoveModel,TypeModel,PokemonModel

class MasterDataService:
    """マスターデータに関するビジネスロジックを担当する"""
    def get_master_data_by_resource(self, resource: str) -> list[dict]:
        """指定されたリソース（テーブル名）からUI表示用のマスターデータをすべて取得する。"""
        if resource not in ['items', 'natures', 'abilities', 'moves', 'types', 'pokemons']:
            raise ValueError(f"Invalid resource: {resource}")
        
        list = []
        if resource == 'pokemons':
            list = PokemonModel.query.order_by(PokemonModel.name_ja).all()
        elif resource == 'natures':
            list = NatureModel.query.order_by(NatureModel.name_ja).all()
        elif resource == 'abilities':
            list = AbilityModel.query.order_by(AbilityModel.name_ja).all()
        elif resource == 'moves':
            list = MoveModel.query.order_by(MoveModel.name_ja).all()
        elif resource == 'types':
            list = TypeModel.query.order_by(TypeModel.name_ja).all()
        elif resource == 'items':
            list = ItemModel.query.order_by(ItemModel.name_ja).all()
        
        return [row.to_dict() for row in list]

    def get_abilities_by_pokemon_id(self, pokemon_id: int) -> list[dict] | None:
        """
        指定されたポケモンIDが持つ特性を取得する。
        ポケモンが存在しない場合はNoneを返す。
        """
        pokemon = PokemonModel.query.get(pokemon_id)
        if not pokemon or not pokemon.abilities:
            return None
        
        ability_ids = [int(id_str) for id_str in pokemon.abilities.split(',') if id_str.strip().isdigit()]
        if not ability_ids:
            return []

        abilities = AbilityModel.query.filter(AbilityModel.id.in_(ability_ids)).all()
        return [row.to_dict() for row in abilities]

    def get_moves_by_pokemon_id(self, pokemon_id: int) -> list[dict] | None:
        """
        指定されたポケモンIDが覚える技を取得する。
        ポケモンが存在しない場合はNoneを返す。
        """
        pokemon = PokemonModel.query.get(pokemon_id)
        if not pokemon or not pokemon.moves:
            return None
        
        move_ids = [int(id_str) for id_str in pokemon.moves.split(',') if id_str.strip().isdigit()]
        if not move_ids:
            return []

        moves = MoveModel.query.filter(MoveModel.id.in_(move_ids)).all()
        return [row.to_dict() for row in moves]