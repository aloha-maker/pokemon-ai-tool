from src.database.manager import db


class RawBattleEventModel(db.Model):
    __tablename__ = 'raw_battle_events'

    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    battle_id = db.Column(db.String, db.ForeignKey('battles.battle_id'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    log_timestamp = db.Column(
        db.String,
        nullable=False,
        default=db.func.strftime('%Y-%m-%d %H:%M:%f', db.func.datetime('now', 'localtime'))
    )
    roi_name = db.Column(db.String, nullable=False)
    ocr_text = db.Column(db.Text)
    phase = db.Column(db.String)

    __table_args__ = (
        db.UniqueConstraint('battle_id', 'sequence', 'roi_name', name='unique_battle_event'),
    )

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "battle_id": self.battle_id,
            "sequence": self.sequence,
            "log_timestamp": self.log_timestamp,
            "roi_name": self.roi_name,
            "ocr_text": self.ocr_text,
            "phase": self.phase,
        }
