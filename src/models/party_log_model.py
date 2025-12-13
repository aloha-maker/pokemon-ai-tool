# C:\pokemon-ai-tool\src\models\party_log_model.py
# from src.database.manager import db
from src.extensions import db 
import json

class PartyLogModel(db.Model):
    __tablename__ = 'parties_log'

    party_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pokemon_id = db.Column(db.Integer, nullable=False)
    battle_id = db.Column(db.String, db.ForeignKey('battles.battle_id'), nullable=False)
    pokemon_name = db.Column(db.String, nullable=False)
    is_opponent = db.Column(db.Boolean, nullable=False)
    is_selected = db.Column(db.Boolean, nullable=False)
    is_first = db.Column(db.Boolean, nullable=False)
    nickname = db.Column(db.String)
    moves = db.Column(db.String)
    terastal_type = db.Column(db.String)
    item = db.Column(db.String)
    ability = db.Column(db.String)


    def to_dict(self):
        return {
            "party_id": self.party_id,
            "battle_id": self.battle_id,
            "pokemon_id": self.pokemon_id,
            "pokemon_name": self.pokemon_name,
            "is_opponent": self.is_opponent,
            "is_selected": self.is_selected,
            "is_first": self.is_first,
            "nickname": self.nickname,
            "moves": json.loads(self.moves) if self.moves else [],
            "terastal_type": self.terastal_type,
            "item": self.item,
            "ability": self.ability,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """辞書からPartyLogModelインスタンスを生成する"""
        return cls(
            pokemon_id=data.get("pokemon_id"),
            battle_id=data.get("battle_id"),
            pokemon_name=data.get("pokemon_name"),
            is_opponent=data.get("is_opponent", False),
            is_selected=data.get("is_selected", False),
            is_first=data.get("is_first", False),
            nickname=data.get("nickname"),
            moves=json.dumps(data.get("moves")) if data.get("moves") else None,
            terastal_type=data.get("terastal_type"),
            item=data.get("item"),
            ability=data.get("ability"),
        )