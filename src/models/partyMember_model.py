from src.database.manager import db
from datetime import datetime

class PartyMemberModel(db.Model):
    __tablename__ = 'party_members'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id', ondelete='CASCADE'), nullable=False)
    trained_pokemon_id = db.Column(db.Integer, db.ForeignKey('trained_pokemons.id', ondelete='CASCADE'), nullable=False)
    member_index = db.Column(db.Integer, nullable=False)  # 0-5

    # 複合ユニーク制約
    __table_args__ = (
        db.UniqueConstraint('party_id', 'trained_pokemon_id', name='uq_party_trained_pokemon'),
        db.UniqueConstraint('party_id', 'member_index', name='uq_party_member_index'),
    )

    # リレーションシップ
    trained_pokemon = db.relationship('TrainedPokemonModel', backref='party_members')

    def to_dict(self):
        return {
            "id": self.id,
            "party_id": self.party_id,
            "trained_pokemon_id": self.trained_pokemon_id,
            "member_index": self.member_index,
            "trained_pokemon": self.trained_pokemon.to_dict() if self.trained_pokemon else None
        }