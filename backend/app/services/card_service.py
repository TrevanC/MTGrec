from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from typing import Optional, List
from app.models.card import ScryfallCard
from app.schemas.card import CardSearchResponse
import json

class CardService:
    def __init__(self, db: Session):
        self.db = db

    async def search_cards(
        self,
        q: Optional[str] = None,
        types: Optional[str] = None,
        color_identity: Optional[str] = None,
        only_commanders: Optional[bool] = False,
        limit: int = 20,
        cursor: Optional[str] = None
    ) -> CardSearchResponse:
        """Search cards with various filters"""

        query = self.db.query(ScryfallCard)

        # Text search
        if q:
            search_conditions = []
            search_term = f"%{q.lower()}%"
            search_conditions.append(ScryfallCard.name.ilike(search_term))
            search_conditions.append(ScryfallCard.oracle_text.ilike(search_term))
            search_conditions.append(ScryfallCard.type_line.ilike(search_term))
            query = query.filter(or_(*search_conditions))

        # Type filter
        if types:
            query = query.filter(ScryfallCard.type_line.ilike(f"%{types}%"))

        # Color identity filter
        if color_identity:
            colors = color_identity.split(",")
            query = query.filter(ScryfallCard.color_identity.contains(colors))

        # Commander filter
        if only_commanders:
            commander_condition = or_(
                and_(
                    ScryfallCard.type_line.ilike("%legendary%"),
                    ScryfallCard.type_line.ilike("%creature%")
                ),
                ScryfallCard.oracle_text.ilike("%can be your commander%"),
                ScryfallCard.oracle_text.ilike("%as a second commander%")
            )
            query = query.filter(commander_condition)

        # Pagination (simple offset-based for now)
        offset = int(cursor) if cursor else 0
        results = query.offset(offset).limit(limit + 1).all()

        # Determine if there are more results
        has_more = len(results) > limit
        if has_more:
            results = results[:limit]

        # Convert to response format
        items = []
        for card in results:
            # Use the full data field which contains the Scryfall object
            card_data = card.data
            items.append(card_data)

        next_cursor = str(offset + limit) if has_more else None

        return CardSearchResponse(items=items, next_cursor=next_cursor)

    async def get_card_by_id(self, card_id: str) -> Optional[dict]:
        """Get a card by its ID"""
        card = self.db.query(ScryfallCard).filter(ScryfallCard.id == card_id).first()
        if card:
            return card.data
        return None

    async def find_card_by_name(self, name: str) -> Optional[ScryfallCard]:
        """Find a card by its name (case insensitive)"""
        return self.db.query(ScryfallCard).filter(
            ScryfallCard.name.ilike(name)
        ).first()

    async def get_cards_by_ids(self, card_ids: List[str]) -> List[ScryfallCard]:
        """Get multiple cards by their IDs"""
        return self.db.query(ScryfallCard).filter(
            ScryfallCard.id.in_(card_ids)
        ).all()