
"""Combine similarity, priors, and heuristics into candidate scores."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence, Tuple

from .commanders import CommanderPriorStore
from .constraints import DeckShapeEvaluator
from .models import CandidateScore, CardRecord, DeckRecord
from .similarity import CardSimilarityModel


@dataclass
class ScoringConfig:
    """Weights for the different scoring components."""

    similarity_weight: float = 0.6
    commander_prior_weight: float = 0.3
    frequency_prior_weight: float = 0.1
    shape_weight: float = 0.05
    max_candidates: int = 500


class CandidateScorer:
    """Produces ranked candidate scores for a given seed deck."""

    def __init__(
        self,
        similarity_model: CardSimilarityModel,
        commander_priors: CommanderPriorStore,
        deck_shape: DeckShapeEvaluator,
        card_lookup: Mapping[str, CardRecord],
        global_frequencies: Mapping[str, int],
        config: ScoringConfig | None = None,
    ) -> None:
        self.similarity_model = similarity_model
        self.commander_priors = commander_priors
        self.deck_shape = deck_shape
        self.card_lookup = card_lookup
        self.global_frequencies = global_frequencies
        self.config = config or ScoringConfig()

    def score_candidates(self, seed: DeckRecord) -> Sequence[CandidateScore]:
        """Return scored candidates for the supplied deck seed."""

        candidate_components: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        similarity_sources: dict[str, list[tuple[str, float]]] = defaultdict(list)
        commander_sources: dict[str, list[str]] = defaultdict(list)
        shape_roles: dict[str, tuple[str, ...]] = {}

        seed_cards = set(seed.card_counts.keys())
        for oracle_id in seed_cards:
            for neighbour_id, similarity in self.similarity_model.neighbors(oracle_id):
                if neighbour_id in seed_cards:
                    continue
                candidate_components[neighbour_id]['similarity'] += similarity
                similarity_sources[neighbour_id].append((oracle_id, similarity))

        prior_scores, prior_sources = self.commander_priors.score(seed.commanders, with_sources=True)
        for oracle_id, value in prior_scores.items():
            if oracle_id in seed_cards:
                continue
            candidate_components[oracle_id]['commander'] += value
            for commander_id, _ in prior_sources.get(oracle_id, ()):
                commander_sources[oracle_id].append(commander_id)

        for oracle_id in list(candidate_components.keys()):
            freq = float(self.global_frequencies.get(oracle_id, 0))
            if freq > 0:
                candidate_components[oracle_id]['frequency'] = math.log1p(freq)

        for oracle_id, components in list(candidate_components.items()):
            card = self.card_lookup.get(oracle_id)
            if not card:
                del candidate_components[oracle_id]
                similarity_sources.pop(oracle_id, None)
                commander_sources.pop(oracle_id, None)
                continue
            shape_delta = self.deck_shape.score_role_adjustment(seed.role_counts, card, delta=1)
            if shape_delta != 0.0:
                components['shape'] = shape_delta
                if card.roles:
                    shape_roles[oracle_id] = tuple(sorted(card.roles))

        scored: list[CandidateScore] = []
        for oracle_id, components in candidate_components.items():
            evidence: dict[str, Tuple[str, ...]] = {}
            if similarity_sources.get(oracle_id):
                top_sources = sorted(
                    similarity_sources[oracle_id], key=lambda item: (-item[1], item[0])
                )[:3]
                evidence['similarity'] = tuple(source for source, _ in top_sources)
            if commander_sources.get(oracle_id):
                ordered = []
                for commander_id in commander_sources[oracle_id]:
                    if commander_id not in ordered:
                        ordered.append(commander_id)
                evidence['commander'] = tuple(ordered)
            if oracle_id in shape_roles:
                evidence['shape'] = shape_roles[oracle_id]
            scored.append(self._combine_components(oracle_id, components, evidence))

        scored.sort(key=lambda item: (-item.total, item.oracle_id))
        if self.config.max_candidates > 0:
            scored = scored[: self.config.max_candidates]
        return scored

    def _combine_components(
        self,
        oracle_id: str,
        components: Mapping[str, float],
        evidence: Mapping[str, Tuple[str, ...]],
    ) -> CandidateScore:
        """Internal helper to package component scores into a dataclass."""

        weighted_total = (
            components.get('similarity', 0.0) * self.config.similarity_weight
            + components.get('commander', 0.0) * self.config.commander_prior_weight
            + components.get('frequency', 0.0) * self.config.frequency_prior_weight
            + components.get('shape', 0.0) * self.config.shape_weight
        )
        return CandidateScore(
            oracle_id=oracle_id,
            total=weighted_total,
            by_component=dict(components),
            evidence=dict(evidence),
        )
