from __future__ import annotations
from typing import Optional, List, Dict, Any

from .party import Party
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
        parties: Optional[List[PartyLogModel]] = None, # 相手パーティと自分パーティ
        events: Optional[List[RawBattleEventModel]] = [],
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BattleLog":
        """
        辞書からBattleLogインスタンスを生成
        
        Args:
            data: BattleLogのデータを含む辞書
            
        Returns:
            BattleLogインスタンス
        """
        # ネストされたモデルの変換
        parties = []
        for party_data in data["parties"]:
            for menber in party_data:
                parties.append(PartyLogModel.from_dict(menber))
        
        events = []
        if "events" in data and data["events"]:
            for event_data in data["events"]:
                if isinstance(event_data, RawBattleEventModel):
                    events.append(event_data)
                else:
                    events.append(RawBattleEventModel(**event_data))
        
        return cls(
            battle_id=data["battle_id"],
            battle_date=data.get("battle_date"),
            season=data.get("season"),
            regulation=data.get("regulation"),
            battle_format=data.get("battle_format"),
            my_rank=data.get("my_rank"),
            opponent_rank=data.get("opponent_rank"),
            result=data.get("result"),
            memo=data.get("memo"),
            parties=parties,
            events=events,
        )

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
            party_log.pokemon_id = 0 # TODO
            db.session.add(party_log)
        
        for event in self.events:
            event.battle_id = model.battle_id
            print("event",event.sequence,event.roi_name,event.ocr_text)
            event.ocr_text = event.ocr_text
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
    # --- イベント操作 ---
    # ======================================================

    def get_latest_sequence_events(self, as_dict: bool = False):
        """
        このバトルログの最新sequenceを持つ全てのイベントを取得する
        
        Args:
            as_dict (bool): Trueの場合、JavaScript用の辞書形式で返す。Falseの場合、イベントのリストを返す
        
        Returns:
            as_dict=False: List[RawBattleEventModel] - 最新sequenceのイベントリスト（複数の場合あり）
            as_dict=True: Dict[str, Dict[str, str]] - {roi_name: {"text": ocr_text}, ...}
            eventsが空の場合は空リスト or 空辞書
        """
        max_sequence = 0
        result = {}
        latest_events = []
        if not self.events:
            if as_dict:
                return result, max_sequence
            else:
                return latest_events, max_sequence
        
        # 最新のsequenceを取得
        max_sequence = max(event.sequence for event in self.events)
        
        # 最新sequenceを持つ全てのイベントを抽出
        latest_events = [event for event in self.events if event.sequence == max_sequence]
        
        # 辞書形式での返却が指定されている場合
        if as_dict:
            
            for event in latest_events:
                if event.roi_name and event.ocr_text:
                    result[event.roi_name] = {
                        "text": event.ocr_text
                    }
            return result,max_sequence
        
        # デフォルトはリスト形式
        return latest_events,max_sequence

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
