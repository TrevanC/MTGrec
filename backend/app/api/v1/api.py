from fastapi import APIRouter
from .endpoints import cards, deck, feedback, health

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(cards.router, prefix="/cards", tags=["cards"])
api_router.include_router(deck.router, prefix="/deck", tags=["deck"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])