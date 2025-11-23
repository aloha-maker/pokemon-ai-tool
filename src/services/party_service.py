# src/services/party_service.py
from typing import List, Dict, Any
import time
from src.extensions import db

from src.schemas.pokemon_battle import Party
from src.schemas.pokemon_battle import Pokemon

from src.schemas.pokemon_battle.party import Party
from src.models.party_model import PartyModel
from src.models.partyMember_model import PartyMemberModel

class PartyService:
    """パーティに関するビジネスロジックを担当する"""
    def get_all(self) -> List[Dict[str, Any]]:
        """すべてのパーティを、メンバー情報を含めて取得する"""
        parties_dict = []
        party_list = PartyModel.query.all()
        for p in party_list:
            party = self.get_by_id(p.id)
            parties_dict.append(party)

        return parties_dict

    def get_by_id(self, party_id: int) -> Dict[str, Any] | None:
        """IDで指定したパーティの情報を、メンバーと技詳細を含めて効率的に取得する。"""
        party = Party.load_from_db(party_id)
        return party.to_dict()

    def create(self, data: Dict[str, Any]) -> int:
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
                    membar = PartyMemberModel(
                        party_id=party.id,
                        trained_pokemon_id=member_id,
                        member_index=index
                    )
                    db.session.add(membar)
            
            db.session.commit()

            return party.id  # 作成したIDを返す

        except Exception as e:
            db.session.rollback()
            raise e

    def update(self, party_id: int, data: Dict[str, Any]) -> int:
        """パーティを更新する"""
        try:
            party = PartyModel.query.get(party_id)
            if not party:
                return False
            PartyModel.query.filter_by(id=party_id).update({
                "name": data["name"],
                "description": data.get("description")
            })
            # メンバー情報を更新            
            for index, member in enumerate(data["members"]):
                PartyMemberModel.query.filter_by(party_id=party_id,member_index=index).update({
                    "trained_pokemon_id": member,
                })
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
        
