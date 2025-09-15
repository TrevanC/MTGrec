from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.deck import (
    ParseDeckRequest, ParsedDeck,
    RecommendRequest, RecommendationsResponse
)
from app.services.deck_service import DeckService
from app.services.recommendation_service import RecommendationService

router = APIRouter()

@router.post("/parse", response_model=ParsedDeck)
async def parse_deck(
    request: ParseDeckRequest,
    db: Session = Depends(get_db)
):
    """Parse a decklist and return normalized deck information"""
    try:
        deck_service = DeckService(db)
        result = await deck_service.parse_decklist(request.decklist)
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/recommend", response_model=RecommendationsResponse)
async def get_recommendations(
    request: RecommendRequest,
    db: Session = Depends(get_db)
):
    """Get upgrade recommendations for a deck"""
    try:
        recommendation_service = RecommendationService(db)
        result = await recommendation_service.get_recommendations(
            commander_ids=request.commander_ids,
            deck_card_ids=request.deck_card_ids,
            budget_cents=request.budget_cents,
            top_k=request.top_k,
            explain=request.explain,
            explain_top_k=request.explain_top_k,
            include_evidence=request.include_evidence,
            include_features=request.include_features
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))