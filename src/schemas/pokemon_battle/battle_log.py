# C:\pokemon-ai-tool\src\schemas\pokemon_battle\battle_log.py
from __future__ import annotations
from typing import Optional, List, Dict

from src.models.battle_model import BattleModel
from src.models.party_log_model import PartyLogModel
from src.models.raw_battle_event_model import RawBattleEventModel


# =========================
# --- バトルスキーマ層 ---
# =========================

class BattleLog:
    """
    ORMのBattleModel, PartyLogModel, RawBattleEventModelを統合的に扱うスキーマ層クラス
    """

    def __init__(
        self,
        battle_id: str,
        battle_date: Optional[str] = None,
        season: Optional[int] = None,
        regulation: Optional[str] = None,
        battle_format: Optional[str] = None,
        my_rank: Optional[int] = None,
        opponent_rank: Optional[int] = None,
        result: Optional[str] = None,
        memo: Optional[str] = None,
        parties: Optional[List[PartyLogModel]] = None,
        events: Optional[List[RawBattleEventModel]] = None,
    ):
        self.battle_id = battle_id
        self.battle_date = battle_date
        self.season = season
        self.regulation = regulation
        self.battle_format = battle_format
        self.my_rank = my_rank
        self.opponent_rank = opponent_rank
        self.result = result
        self.memo = memo
        self.parties = parties or []
        self.events = events or []

    # ======================================================
    # --- ORM層との変換 ---
    # ======================================================

    @classmethod
    def from_model(cls, model: BattleModel) -> "BattleLog":
        """DBのBattleModelからBattleインスタンスを生成"""
        battle = cls(
            battle_id=model.battle_id,
            battle_date=model.battle_date,
            season=model.season,
            regulation=model.regulation,
            battle_format=model.battle_format,
            my_rank=model.my_rank,
            opponent_rank=model.opponent_rank,
            result=model.result,
            memo=model.memo,
            parties=model.parties,
            events=model.events,
        )
        return battle

    def to_model(self) -> BattleModel:
        """BattleインスタンスからBattleModelを生成"""
        model = BattleModel(
            battle_id=self.battle_id,
            battle_date=self.battle_date,
            season=self.season,
            regulation=self.regulation,
            battle_format=self.battle_format,
            my_rank=self.my_rank,
            opponent_rank=self.opponent_rank,
            result=self.result,
            memo=self.memo,
        )
        return model

    # ======================================================
    # --- DB操作ラッパー ---
    # ======================================================

    def save_to_db(self) -> None:
        """BattleをDBに保存"""
        from src.extensions import db

        model = self.to_model()
        db.session.add(model)
        db.session.commit()

        # PartyLogやEventも保存
        for party_log in self.parties:
            party_log.battle_id = model.battle_id
            db.session.add(party_log)
        
        for event in self.events:
            event.battle_id = model.battle_id
            db.session.add(event)

        db.session.commit()

    @classmethod
    def load_from_db(cls, battle_id: str) -> Optional["BattleLog"]:
        """DBからBattleを読み込み"""
        model = BattleModel.query.get(battle_id)
        if model:
            return cls.from_model(model)
        return None

    @classmethod
    def load_all_from_db(cls) -> List["BattleLog"]:
        """DBからすべてのバトルを読み込み"""
        models = BattleModel.query.all()
        return [cls.from_model(m) for m in models]

    # ======================================================
    # --- ユーティリティ ---
    # ======================================================

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "battle_id": self.battle_id,
            "battle_date": self.battle_date,
            "season": self.season,
            "regulation": self.regulation,
            "battle_format": self.battle_format,
            "my_rank": self.my_rank,
            "opponent_rank": self.opponent_rank,
            "result": self.result,
            "memo": self.memo,
            "parties": [p.to_dict() for p in self.parties],
            "events": [e.to_dict() for e in self.events],
        }

    def __str__(self) -> str:
        return f"Battle({self.battle_id}, {self.result}, {self.battle_format})"
