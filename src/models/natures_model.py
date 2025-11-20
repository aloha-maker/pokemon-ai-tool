from src.extensions import db

class NatureModel(db.Model):
    __tablename__ = "natures"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    name_ja = db.Column(db.String)
    increased_stat = db.Column(db.String)
    decreased_stat = db.Column(db.String)

    def __repr__(self):
        return f"<Nature {self.id}: {self.name}>"
