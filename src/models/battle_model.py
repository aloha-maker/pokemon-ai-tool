from src.extensions import db

class BattleModel(db.Model):
    __tablename__ = 'battles'

    battle_id = db.Column(db.String, primary_key=True)
    battle_date = db.Column(
        db.String,
        nullable=False,
        default=db.func.datetime('now', 'localtime')
    )
    season = db.Column(db.Integer)
    regulation = db.Column(db.String)
    battle_format = db.Column(
        db.String,
        nullable=False
    )
    my_rank = db.Column(db.Integer)
    opponent_rank = db.Column(db.Integer)
    result = db.Column(
        db.String,
        nullable=False
    )
    memo = db.Column(db.Text)

    # リレーション
    parties = db.relationship('PartyLogModel', backref='battle', cascade='all, delete-orphan')
    events = db.relationship('RawBattleEventModel', backref='battle', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "battle_id": self.battle_id,
            "battle_date": self.battle_date,
            "season": self.season,
            "regulation": self.regulation,
            "battle_format": self.battle_format,
            "my_rank": self.my_rank,
            "opponent_rank": self.opponent_rank,
            "result": self.result,
            "memo": self.memo,
        }