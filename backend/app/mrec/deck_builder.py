
"""Assemble ranked outputs and full deck recommendations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .constraints import ConstraintChecker, DeckShapeEvaluator
from .models import CandidateScore, CardRecord, DeckRecommendation, DeckRecord, RecommendationReason, SwapSuggestion


@dataclass
class DeckBuilderConfig:
    """Configuration for deck completion and swap thresholds."""

    target_size: int = 100
    min_score_delta: float = 0.1
    ranked_list_size: int = 25
    max_swaps: int = 5


class DeckAssembler:
    """Produces the human-facing recommendation artefacts."""

    def __init__(
        self,
        constraint_checker: ConstraintChecker,
        deck_shape: DeckShapeEvaluator,
        card_lookup: Mapping[str, CardRecord],
        global_frequencies: Mapping[str, int],
        config: DeckBuilderConfig | None = None,
    ) -> None:
        self.constraint_checker = constraint_checker
        self.deck_shape = deck_shape
        self.card_lookup = card_lookup
        self.global_frequencies = global_frequencies
        self.config = config or DeckBuilderConfig()

    def build_ranked_list(self, scores: Sequence[CandidateScore]) -> Sequence[tuple[CandidateScore, RecommendationReason]]:
        """Return the top-N candidate scores paired with explanations."""

        top = scores[: self.config.ranked_list_size]
        results: list[tuple[CandidateScore, RecommendationReason]] = []
        for score in top:
            reason = self._reason_from_score(score)
            results.append((score, reason))
        return results

    def build_full_deck(
        self,
        seed: DeckRecord,
        ranked_scores: Sequence[CandidateScore],
    ) -> DeckRecommendation:
        """Construct a completed deck and swap suggestions."""

        target = self.config.target_size
        current_cards = list(seed.cards)
        current_counts = dict(seed.card_counts)
        role_counts = dict(seed.role_counts)

        additions: list[str] = []
        removals: list[str] = []
        swaps: list[SwapSuggestion] = []

        legal_candidates = [
            score
            for score in ranked_scores
            if self.constraint_checker.is_legal_addition(seed, score.oracle_id, existing_counts=current_counts)
        ]

        if len(current_cards) < target:
            for score in legal_candidates:
                if len(current_cards) >= target:
                    break
                card_id = score.oracle_id
                card = self.card_lookup.get(card_id)
                if card is None:
                    continue
                current_cards.append(card_id)
                current_counts[card_id] = current_counts.get(card_id, 0) + 1
                self._update_role_counts(role_counts, card, delta=1)
                additions.append(card_id)
        else:
            for score in legal_candidates:
                if len(swaps) >= self.config.max_swaps:
                    break
                card_id = score.oracle_id
                if current_counts.get(card_id, 0) > 0:
                    continue
                card = self.card_lookup.get(card_id)
                if card is None:
                    continue
                removal_id = self._select_removal_candidate(seed, current_counts, role_counts)
                if removal_id is None:
                    continue
                removal_card = self.card_lookup.get(removal_id)
                if removal_card is None:
                    continue
                current_counts[removal_id] -= 1
                current_cards.remove(removal_id)
                self._update_role_counts(role_counts, removal_card, delta=-1)
                removals.append(removal_id)

                current_cards.append(card_id)
                current_counts[card_id] = current_counts.get(card_id, 0) + 1
                self._update_role_counts(role_counts, card, delta=1)
                additions.append(card_id)

                reason = self._reason_from_score(score)
                swaps.append(
                    SwapSuggestion(
                        outgoing=removal_id,
                        incoming=card_id,
                        reason=reason,
                    )
                )

        notes: list[str] = []
        if len(current_cards) != target:
            notes.append(f"Deck has {len(current_cards)} cards; target is {target}.")

        return DeckRecommendation(
            cards=tuple(current_cards),
            additions=tuple(additions),
            removals=tuple(removals),
            swaps=tuple(swaps),
            role_summary=dict(role_counts),
            notes=tuple(notes),
        )

    # ------------------------------------------------------------------
    # internal helpers

    def _reason_from_score(self, score: CandidateScore) -> RecommendationReason:
        components = score.by_component
        evidence = score.evidence
        summaries: list[str] = []
        supporting: list[str] = []
        roles: tuple[str, ...] = evidence.get('shape', ())

        sim_cards = evidence.get('similarity', ())
        if sim_cards:
            names = ', '.join(self._card_name(cid) for cid in sim_cards[:2])
            summaries.append(f"Frequently seen with {names}")
            supporting.extend(sim_cards)

        commander_cards = evidence.get('commander', ())
        if commander_cards:
            names = ', '.join(self._card_name(cid) for cid in commander_cards[:2])
            summaries.append(f"Commander synergy: {names}")
            supporting.extend(commander_cards)

        if components.get('frequency'):
            summaries.append('Popular across observed decks')

        if roles:
            role_list = ', '.join(roles[:3])
            summaries.append(f"Supports {role_list} role")

        if not summaries:
            summaries.append('Promising upgrade candidate')

        unique_support = tuple(dict.fromkeys(supporting))
        return RecommendationReason(
            summary='; '.join(summaries),
            supporting_cards=unique_support,
            roles=roles,
        )

    def _update_role_counts(self, role_counts: dict[str, int], card: CardRecord, delta: int) -> None:
        for role in card.roles:
            role_counts[role] = role_counts.get(role, 0) + delta
            if role_counts[role] <= 0:
                role_counts.pop(role, None)

    def _select_removal_candidate(
        self,
        seed: DeckRecord,
        current_counts: Mapping[str, int],
        role_counts: Mapping[str, int],
    ) -> str | None:
        worst_card: str | None = None
        worst_score = float('inf')
        for card_id, count in current_counts.items():
            if count <= 0 or card_id in seed.commanders:
                continue
            card = self.card_lookup.get(card_id)
            if card is None:
                continue
            freq = self.global_frequencies.get(card_id, 0)
            freq_score = math.log1p(freq)
            shape_effect = -self.deck_shape.score_role_adjustment(role_counts, card, delta=-1)
            total_score = freq_score + max(shape_effect, 0.0)
            if total_score < worst_score:
                worst_score = total_score
                worst_card = card_id
        return worst_card

    def _card_name(self, oracle_id: str) -> str:
        card = self.card_lookup.get(oracle_id)
        return card.name if card and card.name else oracle_id
