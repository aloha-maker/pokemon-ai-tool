from src.extensions import db

class PokemonModel(db.Model):
    __tablename__ = 'pokemons'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    name_ja = db.Column(db.String)
    base_id = db.Column(db.Integer)
    type1 = db.Column(db.String, nullable=False)
    type2 = db.Column(db.String)
    hp = db.Column(db.Integer, nullable=False)
    attack = db.Column(db.Integer, nullable=False)
    defense = db.Column(db.Integer, nullable=False)
    sp_attack = db.Column(db.Integer, nullable=False)
    sp_defense = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Integer, nullable=False)
    moves = db.Column(db.String)
    abilities = db.Column(db.String)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_ja": self.name_ja,
            "type1": self.type1,
            "type2": self.type2,
            "hp": self.hp,
            "attack": self.attack,
            "defense": self.defense,
            "sp_attack": self.sp_attack,
            "sp_defense": self.sp_defense,
            "speed": self.speed,
            "moves": self.moves.split(',') if self.moves else [],
            "abilities": self.abilities.split(',') if self.abilities else [],
        }