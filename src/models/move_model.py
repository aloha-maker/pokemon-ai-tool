from src.database.manager import db

class MoveModel(db.Model):
    __tablename__ = 'moves'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    name_ja = db.Column(db.String)
    type = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    power = db.Column(db.Integer)
    accuracy = db.Column(db.Integer)
    pp = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_ja": self.name_ja,
            "type": self.type,
            "category": self.category,
            "power": self.power,
            "accuracy": self.accuracy,
            "pp": self.pp,
        }