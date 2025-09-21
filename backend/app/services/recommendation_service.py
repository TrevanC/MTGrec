import hashlib
import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.card import ScryfallCard
from app.models.stats import CoOccurrenceStats
from app.schemas.deck import (
    RecommendationsResponse, Recommendation, RecommendContext,
    RecommendationExplanation, ExplanationReason, ExplanationEvidence
)
from app.services.card_service import CardService
from app.mrec.inference import InferenceRecommender

class RecommendationService:
    def __init__(self, db: Session, inference_recommender: InferenceRecommender):
        self.db = db
        self.card_service = CardService(db)
        self.inference_recommender = inference_recommender

    async def get_recommendations(
        self,
        commander_ids: List[str],
        deck_card_ids: List[str],
        budget_cents: int = 5000,
        top_k: int = 20,
        explain: str = "full",
        explain_top_k: int = 10,
        include_evidence: bool = False,
        include_features: bool = False,
        allow_unresolved: bool = True
    ) -> RecommendationsResponse:
        """Generate upgrade recommendations for a deck"""

        # Get deck cards for context
        commanders = await self.card_service.get_cards_by_ids(commander_ids) if commander_ids else []
        deck_cards = await self.card_service.get_cards_by_ids(deck_card_ids) if deck_card_ids else []

        if not commanders:
            raise ValueError("No valid commanders found")

        # Calculate deck hash for context
        deck_hash = self._calculate_deck_hash(commander_ids + deck_card_ids)

        # Get color identity from commanders
        color_identity = set()
        for commander in commanders:
            if isinstance(commander.color_identity, list):
                color_identity.update(commander.color_identity)

        recommendations: List[Recommendation] = []

        try:
            # Use the InferenceRecommender to get recommendations
            recommendations = await self._get_inference_recommendations(
                commanders=commanders,
                deck_cards=deck_cards,
                top_n=top_k,
                allow_unresolved=allow_unresolved
            )
        except Exception as e:
            # log error, return empty recommendations
            logging.error(f"InferenceRecommender failed: {e}")
            

        # Create response
        context = RecommendContext(
            commander_ids=commander_ids,
            deck_cards_hash=deck_hash,
            color_identity=sorted(color_identity),
            filters={"budget_cents": budget_cents}
        )

        return RecommendationsResponse(
            algo_version="2025-09-14a",
            context=context,
            recommendations=recommendations[:top_k]
        )

 
    async def _get_inference_recommendations(
        self,
        commanders: List[ScryfallCard],
        deck_cards: List[ScryfallCard],
        top_n: int = 20,
        allow_unresolved: bool = True
    ) -> List[Recommendation]:
        """Get recommendations using the InferenceRecommender"""
        try:
            # Get oracle IDs for commanders and deck cards
            card_identifiers = []

            # Add commander oracle IDs
            for commander in commanders:
                card_identifiers.append(commander.oracle_id)
            
            # Add deck card oracle IDs
            for card in deck_cards:
                card_identifiers.append(card.oracle_id)

            # invoke inference recommender
            result = self.inference_recommender.recommend(
                card_identifiers=card_identifiers,
                top_n=top_n,
                allow_unresolved=allow_unresolved
            )

            # unsolved identifiers, might be new cards that the recommender was not trained on
            unresolved = result.unresolved

            # ranked are recommendations, with scores
            ranked = result.ranked

            # swapped are swaps suggested to improve the deck
            swaps = result.deck.swaps
            
            # Convert InferenceRecommender results to our Recommendation format
            recommendations = []
            for score, reason in ranked:
                # Get card data from the inference recommender
                engine_card = self.inference_recommender.get_card_by_oracle_id(score.oracle_id)
                if engine_card:
                    # get scryfall card
                    scryfall_card = await self.card_service.get_card_by_oracle_id(engine_card.oracle_uid) if engine_card.oracle_uid else None

                    # Convert CardRecord to our expected format
                    card_data = scryfall_card
                    
                    recommendation = Recommendation(
                        card=card_data or {
                            "id": score.oracle_id,
                            "name": engine_card.name,
                        },
                        score=score.total,
                        explanation=RecommendationExplanation(
                            summary=f"MagicRec (20k public decks)",
                            reasons=[
                                # TODO: add more information in CandidateScore and RecommendationReason
                                ExplanationReason(
                                    type="inference_score",
                                    detail=f"Score: {score.total:.3f}, reason: {reason.summary}",
                                    # use the total score as weight for now
                                    weight=score.total
                                )
                            ]
                        )
                    )
                    recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            # Log error and return empty recommendations if inference fails
            logging.warning(f"InferenceRecommender failed: {e}")

        # TODO: return swaps, which is very cool.
        return recommendations

    def _calculate_deck_hash(self, card_ids: List[str]) -> str:
        """Calculate a hash for the deck composition"""
        sorted_ids = sorted(card_ids)
        deck_string = ''.join(sorted_ids)
        return hashlib.sha256(deck_string.encode()).hexdigest()[:16]