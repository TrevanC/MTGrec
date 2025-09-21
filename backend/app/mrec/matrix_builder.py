
"""Construct the sparse deck-card matrix and aggregated statistics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

from .models import DeckDataset, MatrixBundle

try:
    from scipy import sparse  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    sparse = None  # type: ignore

try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    tqdm = None  # type: ignore


@dataclass
class MatrixBuilderConfig:
    """Configuration values for matrix construction."""

    min_card_frequency: int = 1  # increase to 3-5 to reduce the matrix size so to speed up computation
    normalize_rows: bool = False


def build_matrix(dataset: DeckDataset, config: MatrixBuilderConfig | None = None, verbose: bool = False) -> MatrixBundle:
    """Create the deck-card matrix plus helper indices from the dataset."""

    if not dataset.decks:
        return MatrixBundle(
            matrix=None,
            card_index={},
            deck_index={},
            card_totals={},
        )

    cfg = config or MatrixBuilderConfig()

    card_totals_counter: Counter[str] = Counter()
    for deck in dataset.decks:
        card_totals_counter.update(deck.card_counts)

    eligible_cards = [
        card_id
        for card_id, total in card_totals_counter.items()
        if total >= cfg.min_card_frequency
    ]
    eligible_cards.sort()

    card_index: Dict[str, int] = {card_id: idx for idx, card_id in enumerate(eligible_cards)}
    deck_index: Dict[str, int] = {
        deck.deck_id: idx for idx, deck in enumerate(dataset.decks)
    }

    if not card_index:
        return MatrixBundle(
            matrix=None,
            card_index=card_index,
            deck_index=deck_index,
            card_totals={},
        )

    row_indices: list[int] = []
    col_indices: list[int] = []
    data_values: list[float] = []
    row_vectors: list[dict[int, float]] = []

    # Create progress bar if verbose and tqdm is available
    deck_iterator = dataset.decks
    if verbose and tqdm is not None:
        deck_iterator = tqdm(dataset.decks, desc='Building matrix rows', unit='deck')

    for deck in deck_iterator:
        row_idx = deck_index[deck.deck_id]
        deck_counts = {
            card_id: count
            for card_id, count in deck.card_counts.items()
            if card_id in card_index
        }
        if not deck_counts:
            row_vectors.append({})
            continue

        row_total = float(sum(deck_counts.values()))
        vector: dict[int, float] = {}
        for card_id, count in deck_counts.items():
            col_idx = card_index[card_id]
            value = count
            if cfg.normalize_rows and row_total > 0:
                value = count / row_total
            row_indices.append(row_idx)
            col_indices.append(col_idx)
            data_values.append(value)
            vector[col_idx] = value
        row_vectors.append(vector)

    matrix_obj: object
    if sparse is not None:
        if verbose:
            print(f'Building sparse matrix with shape ({len(dataset.decks)}, {len(card_index)})')
        shape = (len(dataset.decks), len(card_index))
        matrix_obj = sparse.csr_matrix((data_values, (row_indices, col_indices)), shape=shape)
    else:
        if verbose:
            print(f'Building dense matrix with shape ({len(dataset.decks)}, {len(card_index)})')
        matrix_obj = tuple(row_vectors)

    card_totals = {card_id: card_totals_counter[card_id] for card_id in card_index}

    return MatrixBundle(
        matrix=matrix_obj,
        card_index=card_index,
        deck_index=deck_index,
        card_totals=card_totals,
    )
