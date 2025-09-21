
"""Hard and soft constraints applied to candidate recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .models import CardRecord, DeckRecord


@dataclass
class DeckShapeTarget:
    """Desired counts for various functional roles within the deck."""

    lands: int = 38
    ramp: int = 10
    draw: int = 10
    removal: int = 10


BASIC_TYPES = {"Basic"}


class ConstraintChecker:
    """Validates candidate cards against hard Commander format rules."""

    def __init__(self, dataset_cards: Mapping[str, CardRecord], ban_list: set[str] | None = None) -> None:
        self.cards = dataset_cards
        self.ban_list = set(ban_list or ())

    def is_legal_addition(
        self, seed: DeckRecord, candidate: str, existing_counts: Mapping[str, int] | None = None
    ) -> bool:
        """Return True if the candidate card satisfies hard constraints."""

        if candidate in self.ban_list:
            return False

        card = self.cards.get(candidate)
        if card is None:
            return False

        if card.legalities.get('commander') != 'legal':
            return False

        allowed_colors = set(seed.color_identity)
        if allowed_colors and not set(card.color_identity).issubset(allowed_colors):
            return False

        counts = existing_counts if existing_counts is not None else seed.card_counts
        if counts.get(candidate, 0) > 0 and not _is_basic_land(card):
            return False

        return True


class DeckShapeEvaluator:
    """Scores how a deck aligns with target role distributions."""

    def __init__(self, target: DeckShapeTarget | None = None) -> None:
        self.target = target or DeckShapeTarget()

    def score_role_adjustment(self, role_counts: Mapping[str, int], card: CardRecord, delta: int) -> float:
        """Evaluate the impact of adding/removing a card on role balance."""

        score = 0.0
        if 'Land' in card.roles:
            score += _role_delta(role_counts.get('Land', 0), self.target.lands, delta)
        if 'Ramp' in card.roles:
            score += _role_delta(role_counts.get('Ramp', 0), self.target.ramp, delta)
        if 'Draw' in card.roles:
            score += _role_delta(role_counts.get('Draw', 0), self.target.draw, delta)
        if 'Removal' in card.roles:
            score += _role_delta(role_counts.get('Removal', 0), self.target.removal, delta)
        return score


# ---------------------------------------------------------------------------
# helper utilities


def _role_delta(current: int, target: int, delta: int) -> float:
    """Simple heuristic: reward moves that close the gap, penalise over-shoot."""

    next_value = current + delta
    before_gap = current - target
    after_gap = next_value - target
    return (abs(before_gap) - abs(after_gap)) / max(target, 1)


def _is_basic_land(card: CardRecord) -> bool:
    return 'Land' in card.types and any(t in BASIC_TYPES for t in card.types)
