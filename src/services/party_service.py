# src/services/party_service.py
from typing import List, Dict, Any
from src.extensions import db

from src.schemas.pokemon_battle import Party
from src.models.party_model import PartyModel,PartyMemberModel

class PartyService:
    """パーティに関するビジネスロジックを担当する"""
    def get_all(self) -> List[Dict[str, Any]]:
        """すべてのパーティを、メンバー情報を含めて取得する"""
        party_list = PartyModel.query.all()
        return [Party.load_from_db(p.id).to_dict() for p in party_list]

    def get_by_id(self, party_id: int) -> Dict[str, Any] | None:
        """IDで指定したパーティの情報を、メンバーと技詳細を含めて効率的に取得する。"""
        party = Party.load_from_db(party_id)
        return party.to_dict()

    def create(self, data: Dict[str, Any]) -> bool:
        """新しいパーティを作成する"""
        try:
            party = PartyModel(
                name=data['name'],
                description=data.get('description', '')
            )
            db.session.add(party)
            db.session.flush()

            members = data.get('members', [])
            if members:
                for index, member_id in enumerate(members):
                    member = PartyMemberModel(
                        party_id=party.id,
                        trained_pokemon_id=member_id,
                        member_index=index
                    )
                    db.session.add(member)
            
            db.session.commit()

            return True

        except Exception as e:
            db.session.rollback()
            raise e

    def update(self, party_id: int, data: Dict[str, Any]) -> bool:
        """パーティを更新する"""
        try:
            party = PartyModel.query.get(party_id)
            if not party:
                return False
            party.name = data["name"]
            party.description = data.get("description")
            # メンバー情報を更新            
            PartyMemberModel.query.filter_by(party_id=party_id).delete()
            for index, member_id in enumerate(data["members"]):
                member = PartyMemberModel(
                    party_id=party_id,
                    trained_pokemon_id=member_id,
                    member_index=index
                )
                db.session.add(member)
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self, party_id: int) -> int:
        """パーティを削除する"""
        try:
            model = PartyModel.query.get(party_id)
            if model:
                db.session.delete(model)
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            raise e
        
