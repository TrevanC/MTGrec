from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.schemas.card import ScryfallCard

class ParseDeckRequest(BaseModel):
    decklist: str
    commander1: Optional[str] = None
    commander2: Optional[str] = None

class DeckIssue(BaseModel):
    type: str
    text: str
    suggestions: Optional[List[str]] = None

class ParsedCard(BaseModel):
    name: str
    set: str
    collector_number: str
    quantity: int

class DecklistCard(BaseModel):
    card: ScryfallCard
    quantity: int

class ParsedDeck(BaseModel):
    commander_ids: List[str]
    commander_names: List[str] = []
    card_ids: List[str]
    color_identity: List[str]
    issues: List[DeckIssue] = []
    decklist: List[DecklistCard] = []

class RecommendRequest(BaseModel):
    commander_ids: List[str]
    deck_card_ids: List[str]
    budget_cents: Optional[int] = 5000
    top_k: Optional[int] = 20
    explain: Optional[str] = "full"  # "none", "preview", "full"
    explain_top_k: Optional[int] = 10
    include_evidence: Optional[bool] = False
    include_features: Optional[bool] = False

class ExplanationReason(BaseModel):
    type: str
    detail: str
    weight: float

class ExplanationEvidence(BaseModel):
    cooc_count: int
    support_decks: int
    window_days: int

class FeatureContribution(BaseModel):
    feature: str
    value: float
    contribution: float

class RecommendationExplanation(BaseModel):
    summary: str
    reasons: List[ExplanationReason]
    evidence: Optional[ExplanationEvidence] = None
    feature_contributions: Optional[List[FeatureContribution]] = None

class Recommendation(BaseModel):
    card: Dict[str, Any]  # ScryfallCard as dict
    score: int
    explanation: RecommendationExplanation

class RecommendContext(BaseModel):
    commander_ids: List[str]
    deck_cards_hash: str
    color_identity: List[str]
    filters: Dict[str, Any]

class RecommendationsResponse(BaseModel):
    algo_version: str
    context: RecommendContext
    recommendations: List[Recommendation]