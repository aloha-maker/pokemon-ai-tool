from src.extensions import db

class NatureModel(db.Model):
    __tablename__ = "natures"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    name_ja = db.Column(db.String)
    increased_stat = db.Column(db.String)
    decreased_stat = db.Column(db.String)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_ja": self.name_ja,
            "increased_stat": self.increased_stat,
            "decreased_stat": self.decreased_stat
        }

    def __repr__(self):
        return f"<Nature {self.id}: {self.name}>"
