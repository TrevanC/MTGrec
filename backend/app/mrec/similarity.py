"""Item-item similarity computation on the deck-card matrix."""

from __future__ import annotations

import math
import pickle
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

from .models import MatrixBundle

try:
    from scipy import sparse  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    sparse = None  # type: ignore

try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    tqdm = None  # type: ignore


@dataclass
class SimilarityConfig:
    """Hyper parameters controlling similarity computation."""

    top_k: int = 200
    min_overlap: int = 2
    shrinkage: float = 0.5  # reduces scores for low-overlap pairs


class CardSimilarityModel:
    """Caches nearest-neighbour similarities for candidate scoring."""

    def __init__(self, config: SimilarityConfig | None = None) -> None:
        self.config = config or SimilarityConfig()
        self._neighbors: Dict[str, list[tuple[str, float]]] = {}
        self._card_index: Dict[str, int] = {}
        self._index_card: Dict[int, str] = {}
        self._freq: Dict[str, int] = {}
        self._fitted = False

    def fit(self, bundle: MatrixBundle, verbose: bool = False) -> None:
        """Compute similarity scores and build neighbour caches."""

        if not bundle.card_index:
            self._reset_state()
            self._fitted = True
            return

        self._card_index = dict(bundle.card_index)
        self._index_card = {idx: cid for cid, idx in bundle.card_index.items()}
        self._freq = dict(bundle.card_totals)

        matrix = bundle.matrix
        if sparse is not None and isinstance(matrix, sparse.csr_matrix):
            if verbose:
                print('Fitting sparse matrix')
            self._neighbors = self._fit_sparse(matrix, verbose=verbose)
        elif isinstance(matrix, Sequence):
            if verbose:
                print('Fitting dense matrix')
            self._neighbors = self._fit_dense_like(matrix, verbose=verbose)
        else:
            raise TypeError('Unsupported matrix representation for similarity computation')

        self._fitted = True

    def neighbors(self, oracle_id: str) -> Sequence[tuple[str, float]]:
        """Return the cached neighbours for a given card."""

        if not self._fitted:
            raise RuntimeError('CardSimilarityModel.fit must be called before querying neighbours')
        return self._neighbors.get(oracle_id, ())

    # ------------------------------------------------------------------
    # internal helpers

    def _fit_sparse(self, matrix: 'sparse.csr_matrix', verbose: bool = False) -> Dict[str, list[tuple[str, float]]]:
        cfg = self.config
        # Binary version to count deck overlap
        binary = matrix.copy().astype(bool).astype(int)
        co_occ = binary.T @ binary
        sim_mat = matrix.T @ matrix

        neighbors: Dict[str, list[tuple[str, float]]] = {}
        
        # Create progress bar if verbose and tqdm is available
        iterator = range(sim_mat.shape[0])
        if verbose and tqdm is not None:
            iterator = tqdm(iterator, desc='Computing card similarities', unit='card')
        
        for idx in iterator:
            card_id = self._index_card[idx]
            row = sim_mat.getrow(idx)
            overlaps = co_occ.getrow(idx)
            candidate_scores: list[tuple[str, float]] = []
            denom_card = self._denominator(card_id)
            if denom_card == 0.0:
                neighbors[card_id] = []
                continue
            for col_idx, dot_value in zip(row.indices, row.data):
                if col_idx == idx:
                    continue
                overlap = overlaps[0, col_idx]
                if overlap < cfg.min_overlap:
                    continue
                other_card_id = self._index_card[col_idx]
                denom_other = self._denominator(other_card_id)
                if denom_other == 0.0:
                    continue
                similarity = dot_value / (denom_card * denom_other)
                similarity *= self._shrink(overlap)
                if similarity <= 0:
                    continue
                candidate_scores.append((other_card_id, similarity))

            neighbors[card_id] = self._top_k(candidate_scores)
        return neighbors

    def _fit_dense_like(self, rows: Sequence[Mapping[int, float]], verbose: bool = False) -> Dict[str, list[tuple[str, float]]]:
        cfg = self.config
        dot_accumulator: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        overlap_counter: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))

        # Create progress bar if verbose and tqdm is available
        iterator = rows
        if verbose and tqdm is not None:
            iterator = tqdm(rows, desc='Computing dense similarities overlaps', unit='row')

        for row in iterator:
            if not row:
                continue
            items = list(row.items())
            for i_idx, i_val in items:
                for j_idx, j_val in items:
                    if i_idx == j_idx:
                        continue
                    dot_accumulator[i_idx][j_idx] += i_val * j_val
                    overlap_counter[i_idx][j_idx] += 1

        # Create progress bar if verbose and tqdm is available
        iterator = dot_accumulator.items()
        if verbose and tqdm is not None:
            iterator = tqdm(dot_accumulator.items(), desc='Computing dense similarities neighbours', unit='row')
        neighbors: Dict[str, list[tuple[str, float]]] = {}
        for idx, others in iterator:
            card_id = self._index_card.get(idx)
            if card_id is None:
                continue
            denom_card = self._denominator(card_id)
            if denom_card == 0.0:
                neighbors[card_id] = []
                continue
            candidate_scores: list[tuple[str, float]] = []
            for other_idx, dot_value in others.items():
                overlap = overlap_counter[idx][other_idx]
                if overlap < cfg.min_overlap:
                    continue
                other_card_id = self._index_card.get(other_idx)
                if other_card_id is None:
                    continue
                denom_other = self._denominator(other_card_id)
                if denom_other == 0.0:
                    continue
                similarity = dot_value / (denom_card * denom_other)
                similarity *= self._shrink(overlap)
                if similarity <= 0:
                    continue
                candidate_scores.append((other_card_id, similarity))
            neighbors[card_id] = self._top_k(candidate_scores)
        return neighbors

    def _denominator(self, card_id: str) -> float:
        freq = max(float(self._freq.get(card_id, 0)), 0.0)
        return math.sqrt(freq) if freq > 0 else 0.0

    def _shrink(self, overlap: int) -> float:
        cfg = self.config
        return overlap / (overlap + cfg.shrinkage) if overlap > 0 else 0.0

    def _top_k(self, scores: Iterable[tuple[str, float]]) -> list[tuple[str, float]]:
        k = self.config.top_k
        sorted_scores = sorted(scores, key=lambda item: (-item[1], item[0]))
        if k <= 0:
            return sorted_scores
        return sorted_scores[:k]


    def save(self, path: str | Path) -> None:
        """Serialize the fitted model to disk for reuse."""

        if not self._fitted:
            raise RuntimeError('Cannot save similarity model before calling fit().')
        payload = {
            'config': self.config.__dict__,
            'neighbors': self._neighbors,
            'card_index': self._card_index,
            'index_card': self._index_card,
            'freq': self._freq,
        }
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('wb') as handle:
            pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def load(cls, path: str | Path) -> "CardSimilarityModel":
        """Load a previously cached similarity model."""

        path = Path(path)
        with path.open('rb') as handle:
            payload = pickle.load(handle)
        config_data = payload.get('config', {})
        config = SimilarityConfig(**config_data)
        model = cls(config)
        model._neighbors = {key: list(map(tuple, value)) for key, value in payload.get('neighbors', {}).items()}
        model._card_index = dict(payload.get('card_index', {}))
        model._index_card = dict(payload.get('index_card', {}))
        model._freq = dict(payload.get('freq', {}))
        model._fitted = True
        return model

    def is_compatible(self, card_index: Mapping[str, int]) -> bool:
        """Return True if the cached model matches the provided card index mapping."""

        return self._card_index == dict(card_index)

    def _reset_state(self) -> None:
        self._neighbors = {}
        self._card_index = {}
        self._index_card = {}
        self._freq = {}
        self._fitted = False
