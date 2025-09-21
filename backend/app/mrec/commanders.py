
"""Commander-conditioned priors and related utilities."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple

from .models import CommanderProfile, DeckRecord


@dataclass
class CommanderPriorConfig:
    """Settings for building and applying commander priors."""

    smoothing: float = 0.01
    max_commanders: int = 2


class CommanderPriorStore:
    """Lookup helper for commander-conditioned card priors."""

    def __init__(self, profiles: Mapping[str, CommanderProfile], config: CommanderPriorConfig | None = None) -> None:
        self.profiles = dict(profiles)
        self.config = config or CommanderPriorConfig()

    def score(
        self,
        commanders: Iterable[str],
        *,
        with_sources: bool = False,
    ) -> Mapping[str, float] | tuple[Mapping[str, float], Mapping[str, Tuple[Tuple[str, float], ...]]]:
        """Blend priors for the supplied commanders into a single score map."""

        selected = list(dict.fromkeys(commanders))[: self.config.max_commanders]
        if not selected:
            return ({}, {}) if with_sources else {}

        blended: Counter[str] = Counter()
        contributions: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        total_weight = 0.0
        for commander_id in selected:
            profile = self.profiles.get(commander_id)
            if not profile or not profile.card_frequency:
                continue
            weight = float(profile.sample_size)
            if weight <= 0:
                continue
            total_weight += weight
            for card_id, freq in profile.card_frequency.items():
                contribution = weight * freq
                blended[card_id] += contribution
                contributions[card_id][commander_id] += contribution

        if total_weight == 0.0:
            return ({}, {}) if with_sources else {}

        smoothing = self.config.smoothing
        denominator = total_weight + smoothing
        scores = {
            card_id: (value + smoothing) / denominator
            for card_id, value in blended.items()
        }

        if not with_sources:
            return scores

        source_map: dict[str, Tuple[Tuple[str, float], ...]] = {}
        for card_id, commander_map in contributions.items():
            total = sum(commander_map.values())
            if total <= 0:
                continue
            ordered = tuple(
                sorted(
                    ((commander_id, amount / total) for commander_id, amount in commander_map.items()),
                    key=lambda item: (-item[1], item[0]),
                )
            )
            if ordered:
                source_map[card_id] = ordered

        return scores, source_map

    @staticmethod
    def build_from_decks(
        decks: Iterable[DeckRecord],
        profiles: Mapping[str, CommanderProfile] | None = None,
        config: CommanderPriorConfig | None = None,
    ) -> 'CommanderPriorStore':
        """Factory helper that constructs priors solely from deck data."""

        if profiles is None:
            raise ValueError('Commander profiles must be precomputed before calling build_from_decks')
        return CommanderPriorStore(profiles=profiles, config=config)
