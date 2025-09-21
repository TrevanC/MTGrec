'''Inference utilities for recommending cards using precomputed models.'''

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .commanders import CommanderPriorStore
from .constraints import ConstraintChecker, DeckShapeEvaluator
from .data_ingest import load_compact_dataset
from .deck_builder import DeckAssembler, DeckBuilderConfig
from .matrix_builder import MatrixBuilderConfig, build_matrix
from .models import (
    CandidateScore,
    DeckDataset,
    DeckRecord,
    DeckRecommendation,
    RecommendationReason,
    CardRecord,
)
from .scoring import CandidateScorer, ScoringConfig
from .similarity import CardSimilarityModel, SimilarityConfig


@dataclass
class RecommendationResult:
    '''Container for inference outputs.'''

    deck: DeckRecommendation
    ranked: Sequence[tuple[CandidateScore, RecommendationReason]]
    unresolved: list[str]


class InferenceRecommender:
    '''Lightweight recommender suitable for web-app inference.'''

    def __init__(
        self,
        dataset_path: str | Path,
        *,
        similarity_cache: str | Path | None = None,
        refresh_cache: bool = False,
        similarity_config: SimilarityConfig | None = None,
        matrix_config: MatrixBuilderConfig | None = None,
        scoring_config: ScoringConfig | None = None,
        deck_builder_config: DeckBuilderConfig | None = None,
        verbose: bool = False,
    ) -> None:
        self.dataset_path = Path(dataset_path)
        self.dataset: DeckDataset = load_compact_dataset(self.dataset_path, show_progress=verbose)

        self.matrix_config = matrix_config or MatrixBuilderConfig()
        self.bundle = build_matrix(self.dataset, self.matrix_config, verbose=verbose)

        self.similarity_config = similarity_config or SimilarityConfig()
        self.similarity_cache = Path(similarity_cache) if similarity_cache else None
        self.similarity = self._load_or_fit_similarity(refresh_cache, verbose=verbose)

        self.deck_shape = DeckShapeEvaluator()
        self.constraint_checker = ConstraintChecker(self.dataset.cards, self.dataset.ban_list)
        self.scoring_config = scoring_config or ScoringConfig()
        ranked_size = deck_builder_config.ranked_list_size if deck_builder_config else 50
        self.deck_builder_config = deck_builder_config or DeckBuilderConfig(
            ranked_list_size=max(ranked_size, 50)
        )

        self.commander_store = CommanderPriorStore(self.dataset.commander_profiles)
        self.scorer = CandidateScorer(
            similarity_model=self.similarity,
            commander_priors=self.commander_store,
            deck_shape=self.deck_shape,
            card_lookup=self.dataset.cards,
            global_frequencies=self.bundle.card_totals,
            config=self.scoring_config,
        )
        self.assembler = DeckAssembler(
            constraint_checker=self.constraint_checker,
            deck_shape=self.deck_shape,
            card_lookup=self.dataset.cards,
            global_frequencies=self.bundle.card_totals,
            config=self.deck_builder_config,
        )

        self._cards_by_oracle = self.dataset.cards
        self._cards_by_uid = {
            card.oracle_uid: card
            for card in self.dataset.cards.values()
            if card.oracle_uid
        }
        self._cards_by_name = {
            card.name.lower(): card
            for card in self.dataset.cards.values()
            if card.name
        }

    def recommend(
        self,
        card_identifiers: Sequence[str],
        *,
        top_n: int = 25,
        allow_unresolved: bool = False,
        seed_record: DeckRecord | None = None,
    ) -> RecommendationResult:
        resolved_ids, unresolved = self._resolve_input_cards(
            card_identifiers, allow_unresolved=allow_unresolved
        )

        if seed_record is None:
            seed_record = self._build_seed_record(resolved_ids)

        scores = self.scorer.score_candidates(seed_record)
        ranked_pairs = self.assembler.build_ranked_list(scores)
        ranked_pairs = ranked_pairs[:top_n]

        deck_rec = self.assembler.build_full_deck(
            seed_record, [score for score, _ in ranked_pairs]
        )

        return RecommendationResult(deck=deck_rec, ranked=ranked_pairs, unresolved=unresolved)

    def get_card_by_oracle_id(self, oracle_id: str) -> CardRecord | None:
        return self._cards_by_oracle.get(oracle_id)

    def get_card_by_uid(self, uid: str) -> CardRecord | None:
        return self._cards_by_uid.get(uid)
    
    def get_card_by_name(self, name: str) -> CardRecord | None:
        return self._cards_by_name.get(name.lower())

    def _load_or_fit_similarity(self, refresh_cache: bool, verbose: bool = False) -> CardSimilarityModel:
        cache_path = self.similarity_cache
        if cache_path and cache_path.exists() and not refresh_cache:
            try:
                model = CardSimilarityModel.load(cache_path)
                if model.is_compatible(self.bundle.card_index):
                    return model
            except Exception:
                pass
        model = CardSimilarityModel(self.similarity_config)
        model.fit(self.bundle, verbose=verbose)
        if cache_path:
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                model.save(cache_path)
            except Exception:
                pass
        return model

    def _resolve_input_cards(
        self, card_identifiers: Sequence[str], *, allow_unresolved: bool
    ) -> tuple[list[str], list[str]]:
        resolved: list[str] = []
        unresolved: list[str] = []

        for identifier in card_identifiers:
            card = self._lookup_card(identifier)
            if card is None:
                unresolved.append(identifier)
                continue
            resolved.append(card.oracle_id)

        if unresolved and not allow_unresolved:
            raise ValueError(
                'Could not resolve the following card identifiers: ' + ', '.join(unresolved)
            )

        if not resolved:
            raise ValueError('No valid cards provided in input identifiers.')

        return resolved, unresolved

    def _lookup_card(self, identifier: str):
        identifier_str = str(identifier)
        if identifier_str in self._cards_by_oracle:
            return self._cards_by_oracle[identifier_str]
        if identifier_str in self._cards_by_uid:
            return self._cards_by_uid[identifier_str]
        identifier_lower = identifier_str.lower()
        return self._cards_by_name.get(identifier_lower)

    def _build_seed_record(self, oracle_ids: Sequence[str]) -> DeckRecord:
        counts = Counter(oracle_ids)
        role_counts: Counter[str] = Counter()
        colors: set[str] = set()
        card_list: list[str] = []

        for oracle_id, quantity in counts.items():
            card = self.dataset.cards.get(oracle_id)
            if not card:
                continue
            card_list.extend([oracle_id] * quantity)
            for role in card.roles:
                role_counts[role] += quantity
            for colour in card.color_identity:
                colors.add(colour)

        return DeckRecord(
            deck_id='inference-seed',
            commanders=tuple(),
            cards=tuple(card_list),
            card_counts=dict(counts),
            color_identity=tuple(sorted(colors)),
            role_counts=dict(role_counts),
        )
