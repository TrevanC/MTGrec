from sqlalchemy import Column, String, Integer, Date, Text, ARRAY, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class ScryfallCard(Base):
    __tablename__ = "scryfall_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    oracle_id = Column(UUID(as_uuid=True))
    name = Column(Text, nullable=False)
    released_at = Column(Date)
    set = Column(Text)
    set_name = Column(Text)
    collector_number = Column(Text)
    lang = Column(Text)
    cmc = Column(Numeric)
    type_line = Column(Text)
    oracle_text = Column(Text)
    colors = Column(ARRAY(Text))
    color_identity = Column(ARRAY(Text), nullable=False)
    keywords = Column(ARRAY(Text))
    legalities = Column(JSON, nullable=False)
    image_uris = Column(JSON)
    card_faces = Column(JSON)
    prices = Column(JSON)
    edhrec_rank = Column(Integer)
    data = Column(JSON, nullable=False)  # Full Scryfall Card object

    def is_commander(self) -> bool:
        """Check if this card can be a commander"""
        type_line = (self.type_line or "").lower()
        oracle_text = (self.oracle_text or "").lower()

        return (
            ("legendary" in type_line and "creature" in type_line) or
            "can be your commander" in oracle_text or
            "as a second commander" in oracle_text
        )