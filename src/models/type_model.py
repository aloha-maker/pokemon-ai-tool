from src.extensions import db

class TypeModel(db.Model):
    __tablename__ = "types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    name_ja = db.Column(db.String)

    def __repr__(self):
        return f"<Type {self.name}>"
