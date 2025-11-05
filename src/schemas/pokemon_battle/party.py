from __future__ import annotations
from typing import Optional, List, Dict
from .pokemon import Pokemon
from src.models.party_model import PartyModel
from src.models.partyMember_model import PartyMemberModel
from src.models.trained_pokemon_moedl import TrainedPokemonModel


# =========================
# --- パーティ ---
# =========================

class Party:
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        members: Optional[List[Pokemon]] = None,
        party_id: Optional[int] = None
    ):
        self.party_id: Optional[int] = party_id
        self.name: str = name
        self.description: Optional[str] = description
        self.members: List[Pokemon] = members if members is not None else []

    def add_member(self, pokemon: Pokemon, index: Optional[int] = None) -> None:
        """メンバーを追加する"""
        if len(self.members) >= 6:
            raise ValueError("パーティは最大6匹までです")
        
        if index is None:
            # 末尾に追加
            self.members.append(pokemon)
        else:
            # 指定位置に追加
            if index < 0 or index > len(self.members):
                raise ValueError("無効なインデックスです")
            self.members.insert(index, pokemon)

    def remove_member(self, index: int) -> None:
        """指定したインデックスのメンバーを削除する"""
        if 0 <= index < len(self.members):
            self.members.pop(index)
        else:
            raise ValueError("無効なインデックスです")

    def get_member(self, index: int) -> Optional[Pokemon]:
        """指定したインデックスのメンバーを取得する"""
        if 0 <= index < len(self.members):
            return self.members[index]
        return None

    def swap_members(self, index1: int, index2: int) -> None:
        """メンバーの順序を入れ替える"""
        if (0 <= index1 < len(self.members) and 
            0 <= index2 < len(self.members)):
            self.members[index1], self.members[index2] = self.members[index2], self.members[index1]
        else:
            raise ValueError("無効なインデックスです")

    def clear_members(self) -> None:
        """すべてのメンバーを削除する"""
        self.members.clear()

    @classmethod
    def from_model(cls, party_model: PartyModel) -> "Party":
        """
        DBのPartyModelからPartyインスタンスを生成する
        """
        party = cls(
            party_id=party_model.id,
            name=party_model.name,
            description=party_model.description
        )

        # メンバーを読み込む（lazy='dynamic'の場合は.all()が必要）
        member_models = party_model.members.all() if hasattr(party_model.members, 'all') else party_model.members
        for member_model in sorted(member_models, key=lambda m: m.member_index):
            trained_pokemon = TrainedPokemonModel.query.get(member_model.trained_pokemon_id)
            if trained_pokemon:
                pokemon = Pokemon.from_trained_model(trained_pokemon)
                party.members.append(pokemon)

        return party

    def to_model(self) -> PartyModel:
        """
        PartyインスタンスからPartyModelを生成する
        """
        party_model = PartyModel(
            name=self.name,
            description=self.description
        )

        # 既存のパーティの場合はIDを設定
        if self.party_id:
            party_model.id = self.party_id

        return party_model

    def save_to_db(self) -> None:
        """
        PartyインスタンスをDBに保存する
        """
        from src.database.manager import db
        
        party_model = self.to_model()
        
        db.session.add(party_model)
        db.session.commit()
        
        # メンバー情報を保存
        for index, pokemon in enumerate(self.members):
            # ここでは仮の実装。実際にはTrainedPokemonModelの保存も必要
            member_model = PartyMemberModel(
                party_id=party_model.id,
                trained_pokemon_id=1,  # 仮の値。実際にはpokemonから取得
                member_index=index
            )
            db.session.add(member_model)
        
        db.session.commit()
        self.party_id = party_model.id

    @classmethod
    def load_from_db(cls, party_id: int) -> Optional["Party"]:
        """
        DBからパーティを読み込む
        """
        party_model = PartyModel.query.get(party_id)
        if party_model:
            return cls.from_model(party_model)
        return None

    @classmethod
    def load_all_from_db(cls) -> List["Party"]:
        """
        DBからすべてのパーティを読み込む
        """
        party_models = PartyModel.query.all()
        return [cls.from_model(model) for model in party_models]

    @classmethod
    def from_dict(cls, data: Dict) -> "Party":
        """
        辞書形式のデータからPartyインスタンスを生成する。
        (to_dictの逆操作)
        """
        
        # 'members' (ポケモンの辞書のリスト) を Pokemon オブジェクトのリストに変換
        # Pokemon.from_dict が存在することを前提とする
        members_list = []
        if "members" in data and data["members"]:
            members_list = [Pokemon.from_dict(pokemon_data) for pokemon_data in data["members"]]
        
        return cls(
            name=data["name"],
            description=data.get("description"), # Optional
            party_id=data.get("party_id"),    # Optional
            members=members_list
        )

    def to_dict(self) -> Dict:
        """
        Partyインスタンスを辞書形式に変換する
        """
        return {
            "party_id": self.party_id,
            "name": self.name,
            "description": self.description,
            "member_count": len(self.members),
            "members": [pokemon.to_dict() for pokemon in self.members],
        }

    def __len__(self) -> int:
        """パーティのメンバー数を返す"""
        return len(self.members)

    def __getitem__(self, index: int) -> Pokemon:
        """インデックスアクセスをサポート"""
        return self.members[index]

    def __str__(self) -> str:
        """文字列表現"""
        member_names = [pokemon.name for pokemon in self.members]
        return f"Party '{self.name}' ({len(self.members)} members): {', '.join(member_names)}"