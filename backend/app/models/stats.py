from sqlalchemy import Column, String, BigInteger, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class CoOccurrenceStats(Base):
    __tablename__ = "cooc_stats"

    context_commander_id = Column(UUID(as_uuid=True), ForeignKey("scryfall_cards.id"), primary_key=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey("scryfall_cards.id"), primary_key=True)
    count = Column(BigInteger, nullable=False)
    last_seen = Column(Date, nullable=False)

    # Relationships
    commander = relationship("ScryfallCard", foreign_keys=[context_commander_id])
    card = relationship("ScryfallCard", foreign_keys=[card_id])

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID(as_uuid=True), ForeignKey("scryfall_cards.id"), nullable=False)
    action = Column(String, nullable=False)  # 'clicked', 'added', 'hidden', 'purchased'
    ts = Column(Date, nullable=False)

    # Relationship
    card = relationship("ScryfallCard")