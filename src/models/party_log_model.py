from src.database.manager import db


class PartyLogModel(db.Model):
    __tablename__ = 'parties_log'

    party_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    battle_id = db.Column(db.String, db.ForeignKey('battles.battle_id'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemons_log.pokemon_id'))
    pokemon_name = db.Column(db.String, nullable=False)
    is_opponent = db.Column(db.Boolean, nullable=False)
    is_selected = db.Column(db.Boolean, nullable=False)

    def to_dict(self):
        return {
            "party_id": self.party_id,
            "battle_id": self.battle_id,
            "pokemon_id": self.pokemon_id,
            "pokemon_name": self.pokemon_name,
            "is_opponent": self.is_opponent,
            "is_selected": self.is_selected,
        }
