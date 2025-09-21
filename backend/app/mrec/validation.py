
"""Offline validation harness for the recommendation pipeline."""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from .models import CardRecord, DeckDataset, DeckRecord
from .scoring import CandidateScorer


@dataclass
class ValidationConfig:
    """Configuration for hold-out experiments and metrics."""

    holdout_fraction: float = 0.1
    seed_size: int = 60
    precision_k: Sequence[int] = (5, 10, 20)
    random_seed: int = 42


@dataclass
class ValidationResult:
    """Aggregated metrics from the validation harness."""

    precision: dict[int, float]
    recall: dict[int, float]
    metadata: dict[str, object]


def run_validation(dataset: DeckDataset, scorer: CandidateScorer, config: ValidationConfig | None = None) -> ValidationResult:
    """Execute hold-out validation and compute summary metrics."""

    cfg = config or ValidationConfig()
    decks = list(dataset.decks)
    if not decks:
        return ValidationResult(precision={}, recall={}, metadata={'evaluated_decks': 0})

    rng = random.Random(cfg.random_seed)
    holdout_size = max(1, min(len(decks), int(len(decks) * cfg.holdout_fraction)))
    holdout_indices = set(rng.sample(range(len(decks)), holdout_size))

    precision_hits: Counter[int] = Counter()
    precision_total: Counter[int] = Counter()
    recall_hits: Counter[int] = Counter()
    recall_total: Counter[int] = Counter()
    evaluated = 0

    for idx, deck in enumerate(decks):
        if idx not in holdout_indices:
            continue

        withheld = set(deck.cards)
        if not withheld:
            continue

        seed_cards = _build_seed_card_list(deck, cfg.seed_size, rng)
        withheld -= set(seed_cards)
        if not withheld:
            continue

        seed_record = _build_seed_record(deck, seed_cards, dataset.cards)
        scores = scorer.score_candidates(seed_record)
        if not scores:
            continue

        evaluated += 1
        for k in cfg.precision_k:
            if k <= 0:
                continue
            top_candidates = [score.oracle_id for score in scores[:k]]
            if not top_candidates:
                continue
            hits = sum(1 for cid in top_candidates if cid in withheld)
            precision_hits[k] += hits
            precision_total[k] += len(top_candidates)
            recall_hits[k] += hits
            recall_total[k] += len(withheld)

    precision = {
        k: (precision_hits[k] / precision_total[k]) if precision_total[k] else 0.0
        for k in cfg.precision_k
    }
    recall = {
        k: (recall_hits[k] / recall_total[k]) if recall_total[k] else 0.0
        for k in cfg.precision_k
    }

    metadata = {
        'evaluated_decks': evaluated,
        'holdout_fraction': cfg.holdout_fraction,
        'seed_size': cfg.seed_size,
        'precision_k': tuple(cfg.precision_k),
    }

    return ValidationResult(precision=precision, recall=recall, metadata=metadata)


def _build_seed_card_list(deck: DeckRecord, target_size: int, rng: random.Random) -> list[str]:
    commanders = list(deck.commanders)
    remaining = [cid for cid in deck.cards if cid not in commanders]
    rng.shuffle(remaining)
    needed = max(0, target_size - len(commanders))
    selected = commanders + remaining[:needed]
    return selected if selected else commanders


def _build_seed_record(
    deck: DeckRecord,
    seed_cards: Sequence[str],
    card_lookup: Mapping[str, CardRecord],
) -> DeckRecord:
    counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    for card_id in seed_cards:
        counts[card_id] += 1
        card = card_lookup.get(card_id)
        if card:
            for role in card.roles:
                role_counts[role] += 1
    return DeckRecord(
        deck_id=f"{deck.deck_id}-seed",
        commanders=deck.commanders,
        cards=tuple(seed_cards),
        card_counts=dict(counts),
        color_identity=deck.color_identity,
        role_counts=dict(role_counts),
    )
