from src.extensions import db

class AbilityModel(db.Model):
    __tablename__ = "abilities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    name_ja = db.Column(db.String)

    def __repr__(self):
        return f"<Ability {self.id}: {self.name}>"