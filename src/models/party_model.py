# from src.database.manager import db
from src.extensions import db 
from datetime import datetime

class PartyModel(db.Model):
    __tablename__ = 'parties'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # リレーションシップの追加
    members = db.relationship(
        'PartyMemberModel', 
        backref='party', 
        cascade='all, delete-orphan',
        lazy='dynamic'  # または 'joined' に変更可能
    )

    def to_dict(self):
        # メンバー情報も含める場合は以下のように変更
        from src.models.partyMember_model import PartyMemberModel
        
        members_data = []
        for member in self.members:
            members_data.append({
                "id": member.id,
                "trained_pokemon_id": member.trained_pokemon_id,
                "member_index": member.member_index
            })
        
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "members": members_data
        }