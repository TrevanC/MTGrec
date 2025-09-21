"""Typed data structures shared across the recommendation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence, Tuple


@dataclass(frozen=True)
class CardRecord:
    """Metadata for a single card identified by its oracle id."""

    oracle_id: str
    oracle_uid: str | None
    name: str
    color_identity: Tuple[str, ...]
    types: Tuple[str, ...]
    mana_value: float
    legalities: Mapping[str, str]
    roles: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DeckRecord:
    """Normalized representation of an Archidekt deck list."""

    deck_id: str
    commanders: Tuple[str, ...]
    cards: Tuple[str, ...]
    card_counts: Mapping[str, int]
    color_identity: Tuple[str, ...]
    role_counts: Mapping[str, int]


@dataclass(frozen=True)
class CommanderProfile:
    """Aggregated statistics for a commander across observed decks."""

    oracle_id: str
    color_identity: Tuple[str, ...]
    card_frequency: Mapping[str, float]
    sample_size: int


@dataclass
class DeckDataset:
    """Container for the ingested decks and lookup tables."""

    decks: Sequence[DeckRecord]
    cards: Mapping[str, CardRecord]
    commander_profiles: Mapping[str, CommanderProfile]
    ban_list: set[str] = field(default_factory=set)


@dataclass
class MatrixBundle:
    """Sparse matrix and helper indices derived from the dataset."""

    matrix: object  # placeholder for scipy.sparse matrix
    card_index: Mapping[str, int]
    deck_index: Mapping[str, int]
    card_totals: Mapping[str, int]


@dataclass
class CandidateScore:
    """Aggregate score for a candidate card with breakdown details."""

    oracle_id: str
    total: float
    by_component: Mapping[str, float]
    evidence: Mapping[str, Tuple[str, ...]]




@dataclass
class RecommendationReason:
    """Human-readable explanation for a recommendation."""

    summary: str
    supporting_cards: Tuple[str, ...]
    roles: Tuple[str, ...] = ()




@dataclass
class SwapSuggestion:
    """Proposed swap from an existing card to a new candidate."""

    outgoing: str
    incoming: str
    reason: RecommendationReason


@dataclass
class DeckRecommendation:
    """Full deck output including swap suggestions and diagnostics."""

    cards: Tuple[str, ...]
    additions: Tuple[str, ...]
    removals: Tuple[str, ...]
    swaps: Tuple[SwapSuggestion, ...]
    role_summary: Mapping[str, int]
    notes: Sequence[str]
