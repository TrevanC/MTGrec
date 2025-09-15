from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.card import ScryfallCard
from app.schemas.card import ScryfallCard as ScryfallCardSchema, CardSearchResponse
from app.services.card_service import CardService

router = APIRouter()

@router.get("", response_model=CardSearchResponse)
async def search_cards(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search query"),
    types: Optional[str] = Query(None, description="Card types filter"),
    color_identity: Optional[str] = Query(None, description="Color identity filter"),
    only_commanders: Optional[bool] = Query(False, description="Only return commander-eligible cards"),
    limit: Optional[int] = Query(20, le=100, description="Maximum number of results"),
    cursor: Optional[str] = Query(None, description="Pagination cursor")
):
    """Search cards with filtering options"""
    try:
        card_service = CardService(db)
        result = await card_service.search_cards(
            q=q,
            types=types,
            color_identity=color_identity,
            only_commanders=only_commanders,
            limit=limit,
            cursor=cursor
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{card_id}", response_model=ScryfallCardSchema)
async def get_card(
    card_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific card by ID"""
    try:
        card_service = CardService(db)
        card = await card_service.get_card_by_id(card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        return card
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))