import hashlib
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.card import ScryfallCard
from app.models.stats import CoOccurrenceStats
from app.schemas.deck import (
    RecommendationsResponse, Recommendation, RecommendContext,
    RecommendationExplanation, ExplanationReason, ExplanationEvidence
)
from app.services.card_service import CardService

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.card_service = CardService(db)

    async def get_recommendations(
        self,
        commander_ids: List[str],
        deck_card_ids: List[str],
        budget_cents: int = 5000,
        top_k: int = 20,
        explain: str = "full",
        explain_top_k: int = 10,
        include_evidence: bool = False,
        include_features: bool = False
    ) -> RecommendationsResponse:
        """Generate upgrade recommendations for a deck"""

        # Get deck cards for context
        commanders = await self.card_service.get_cards_by_ids(commander_ids)
        deck_cards = await self.card_service.get_cards_by_ids(deck_card_ids)

        if not commanders:
            raise ValueError("No valid commanders found")

        # Calculate deck hash for context
        deck_hash = self._calculate_deck_hash(commander_ids + deck_card_ids)

        # Get color identity from commanders
        color_identity = set()
        for commander in commanders:
            if commander.color_identity:
                color_identity.update(commander.color_identity)

        # Get recommendations using co-occurrence data
        recommendations = await self._get_cooccurrence_recommendations(
            commanders=commanders,
            deck_cards=deck_cards,
            budget_cents=budget_cents,
            top_k=top_k,
            color_identity=list(color_identity)
        )

        # Generate explanations
        if explain != "none":
            recommendations = await self._add_explanations(
                recommendations,
                commanders,
                deck_cards,
                explain_full=(explain == "full"),
                explain_top_k=explain_top_k,
                include_evidence=include_evidence,
                include_features=include_features
            )

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

    async def _get_cooccurrence_recommendations(
        self,
        commanders: List[ScryfallCard],
        deck_cards: List[ScryfallCard],
        budget_cents: int,
        top_k: int,
        color_identity: List[str]
    ) -> List[Recommendation]:
        """Get recommendations based on co-occurrence statistics"""

        recommendations = []
        deck_card_ids = {str(card.id) for card in deck_cards}

        # Query co-occurrence stats for each commander
        for commander in commanders:
            query = self.db.query(CoOccurrenceStats, ScryfallCard).join(
                ScryfallCard, CoOccurrenceStats.card_id == ScryfallCard.id
            ).filter(
                CoOccurrenceStats.context_commander_id == commander.id
            )

            # Filter by color identity
            if color_identity:
                query = query.filter(
                    ScryfallCard.color_identity.contained_by(color_identity)
                )

            # Filter by budget
            if budget_cents > 0:
                # Filter cards that have price info and are within budget
                # This is a simplified filter - in production you'd want more sophisticated price handling
                query = query.filter(
                    ScryfallCard.data['prices']['usd'].astext.cast(float) <= (budget_cents / 100.0)
                )

            # Exclude cards already in deck
            query = query.filter(
                ~ScryfallCard.id.in_([card.id for card in deck_cards])
            )

            # Order by co-occurrence count
            results = query.order_by(CoOccurrenceStats.count.desc()).limit(top_k * 2).all()

            for cooc_stat, card in results:
                if str(card.id) not in deck_card_ids:
                    rec = Recommendation(
                        card=card.data,
                        score=cooc_stat.count,
                        explanation=RecommendationExplanation(
                            summary=f"Popular with {commander.name}",
                            reasons=[]
                        )
                    )
                    recommendations.append(rec)

        # Sort by score and remove duplicates
        seen_cards = set()
        unique_recommendations = []

        for rec in sorted(recommendations, key=lambda x: x.score, reverse=True):
            card_id = rec.card['id']
            if card_id not in seen_cards:
                seen_cards.add(card_id)
                unique_recommendations.append(rec)

        return unique_recommendations[:top_k * 2]  # Return more than needed for filtering

    async def _add_explanations(
        self,
        recommendations: List[Recommendation],
        commanders: List[ScryfallCard],
        deck_cards: List[ScryfallCard],
        explain_full: bool = True,
        explain_top_k: int = 10,
        include_evidence: bool = False,
        include_features: bool = False
    ) -> List[Recommendation]:
        """Add explanations to recommendations"""

        for i, rec in enumerate(recommendations):
            # Only add full explanations for top_k cards
            should_explain_full = explain_full and i < explain_top_k

            if should_explain_full:
                reasons = [
                    ExplanationReason(
                        type="co_occurrence",
                        detail=f"Frequently played with your commander",
                        weight=0.8
                    ),
                    ExplanationReason(
                        type="color_identity",
                        detail="Fits your deck's color identity",
                        weight=0.2
                    )
                ]

                explanation = RecommendationExplanation(
                    summary=f"Strong synergy with {commanders[0].name}",
                    reasons=reasons
                )

                if include_evidence:
                    explanation.evidence = ExplanationEvidence(
                        cooc_count=rec.score,
                        support_decks=rec.score,  # Simplified
                        window_days=90
                    )

                rec.explanation = explanation

        return recommendations

    def _calculate_deck_hash(self, card_ids: List[str]) -> str:
        """Calculate a hash for the deck composition"""
        sorted_ids = sorted(card_ids)
        deck_string = ''.join(sorted_ids)
        return hashlib.sha256(deck_string.encode()).hexdigest()[:16]