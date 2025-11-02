# from src.database.manager import db
from src.extensions import db 
from datetime import datetime

class TrainedPokemonModel(db.Model):
    __tablename__ = 'trained_pokemons'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemons.id'), nullable=False)
    nickname = db.Column(db.String)
    level = db.Column(db.Integer, nullable=False, default=50)
    tera_type_id = db.Column(db.Integer, db.ForeignKey('types.id'))
    ability_id = db.Column(db.Integer, db.ForeignKey('abilities.id'))
    nature_id = db.Column(db.Integer, db.ForeignKey('natures.id'))
    held_item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    move1_id = db.Column(db.Integer, db.ForeignKey('moves.id'))
    move2_id = db.Column(db.Integer, db.ForeignKey('moves.id'))
    move3_id = db.Column(db.Integer, db.ForeignKey('moves.id'))
    move4_id = db.Column(db.Integer, db.ForeignKey('moves.id'))
    ev_hp = db.Column(db.Integer, default=0)
    ev_atk = db.Column(db.Integer, default=0)
    ev_def = db.Column(db.Integer, default=0)
    ev_spa = db.Column(db.Integer, default=0)
    ev_spd = db.Column(db.Integer, default=0)
    ev_spe = db.Column(db.Integer, default=0)
    iv_hp = db.Column(db.Integer, default=31)
    iv_atk = db.Column(db.Integer, default=31)
    iv_def = db.Column(db.Integer, default=31)
    iv_spa = db.Column(db.Integer, default=31)
    iv_spd = db.Column(db.Integer, default=31)
    iv_spe = db.Column(db.Integer, default=31)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "pokemon_id": self.pokemon_id,
            "nickname": self.nickname,
            "level": self.level,
            "tera_type_id": self.tera_type_id,
            "ability_id": self.ability_id,
            "nature_id": self.nature_id,
            "held_item_id": self.held_item_id,
            "move1_id": self.move1_id,
            "move2_id": self.move2_id,
            "move3_id": self.move3_id,
            "move4_id": self.move4_id,
            "ev_hp": self.ev_hp,
            "ev_atk": self.ev_atk,
            "ev_def": self.ev_def,
            "ev_spa": self.ev_spa,
            "ev_spd": self.ev_spd,
            "ev_spe": self.ev_spe,
            "iv_hp": self.iv_hp,
            "iv_atk": self.iv_atk,
            "iv_def": self.iv_def,
            "iv_spa": self.iv_spa,
            "iv_spd": self.iv_spd,
            "iv_spe": self.iv_spe,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }