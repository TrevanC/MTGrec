from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import os
from datetime import datetime
from app.core.database import get_db
from app.schemas.deck import (
    ParseDeckRequest, ParsedDeck,
    RecommendRequest, RecommendationsResponse
)
from app.services.deck_service import DeckService
from app.services.recommendation_service import RecommendationService
from app.mrec.inference import InferenceRecommender
from app.core.inference import get_inference_recommender
from app.core.config import settings

router = APIRouter()

def get_recommendation_service(db: Session = Depends(get_db)) -> RecommendationService:
    """Get RecommendationService with InferenceRecommender dependency"""
    inference_recommender = get_inference_recommender()
    return RecommendationService(db, inference_recommender)

def dump_request_to_json(request_data: dict, endpoint: str):
    """Dump request data to a JSON file with timestamp (only in debug mode)"""
    if not settings.DEBUG:
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"request_{endpoint}_{timestamp}.json"
    
    # Create requests directory if it doesn't exist
    requests_dir = "debug"
    if not os.path.exists(requests_dir):
        os.makedirs(requests_dir)
    
    filepath = os.path.join(requests_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(request_data, f, indent=2, default=str)
    
    print(f"Request dumped to: {filepath}")
    return filepath

def dump_response_to_json(response_data: dict, endpoint: str):
    """Dump response data to a JSON file with timestamp (only in debug mode)"""
    if not settings.DEBUG:
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"response_{endpoint}_{timestamp}.json"
    
    # Create responses directory if it doesn't exist
    responses_dir = "debug"
    if not os.path.exists(responses_dir):
        os.makedirs(responses_dir)
    
    filepath = os.path.join(responses_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(response_data, f, indent=2, default=str)
    
    print(f"Response dumped to: {filepath}")
    return filepath

@router.post("/parse", response_model=ParsedDeck)
async def parse_deck(
    request: ParseDeckRequest,
    db: Session = Depends(get_db)
):
    """Parse a decklist and return normalized deck information"""
    try:
        # Dump request to JSON file
        request_data = {
            "endpoint": "parse",
            "timestamp": datetime.now().isoformat(),
            "request": request.model_dump()
        }
        dump_request_to_json(request_data, "parse")
        
        deck_service = DeckService(db)
        result = await deck_service.parse_decklist(
            request.decklist, 
            request.commander1, 
            request.commander2
        )
        
        # Dump response to JSON file
        response_data = {
            "endpoint": "parse",
            "timestamp": datetime.now().isoformat(),
            "response": result.model_dump()
        }
        dump_response_to_json(response_data, "parse")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/recommend", response_model=RecommendationsResponse)
async def get_recommendations(
    request: RecommendRequest,
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    """Get upgrade recommendations for a deck"""
    try:
        # Dump request to JSON file
        request_data = {
            "endpoint": "recommend",
            "timestamp": datetime.now().isoformat(),
            "request": request.model_dump()
        }
        dump_request_to_json(request_data, "recommend")
        
        result = await recommendation_service.get_recommendations(
            commander_ids=request.commander_ids,
            deck_card_ids=request.deck_card_ids,
            budget_cents=request.budget_cents or 5000,
            top_k=request.top_k or 20,
            explain=request.explain or "full",
            explain_top_k=request.explain_top_k or 10,
            include_evidence=request.include_evidence or False,
            include_features=request.include_features or False,
            allow_unresolved=request.allow_unresolved if request.allow_unresolved is not None else True
        )
        
        # Dump response to JSON file
        response_data = {
            "endpoint": "recommend",
            "timestamp": datetime.now().isoformat(),
            "response": result.model_dump()
        }
        dump_response_to_json(response_data, "recommend")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))