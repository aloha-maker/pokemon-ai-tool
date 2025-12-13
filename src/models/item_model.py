from src.extensions import db

class ItemModel(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    name_ja = db.Column(db.String)
    category = db.Column(db.String)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "name_ja": self.name_ja,
            "category": self.category
        }

    def __repr__(self):
        return f"<Item {self.id}: {self.name}>"