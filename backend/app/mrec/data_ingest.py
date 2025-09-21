
"""Load and normalize Archidekt deck exports into internal data structures."""

from __future__ import annotations

import gzip
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

try:
    from tqdm import tqdm
except Exception:
    tqdm = None  # type: ignore

from .models import CardRecord, CommanderProfile, DeckDataset, DeckRecord


@dataclass
class ParsedDeck:
    """Container bundling a parsed deck record with card metadata."""

    record: DeckRecord
    cards: dict[str, CardRecord]


def load_deck_dataset(data_dir: Path, show_progress: bool = False) -> DeckDataset:
    """Read every JSON deck export and assemble the aggregated dataset."""

    deck_records: list[DeckRecord] = []
    parsed_decks: list[ParsedDeck] = []

    deck_files = list(iter_deck_files(data_dir))
    iterator = deck_files
    if show_progress and tqdm is not None:
        iterator = tqdm(deck_files, desc='Loading decks', unit='deck')

    for deck_file in iterator:
        parsed = parse_deck_file(deck_file)
        parsed_decks.append(parsed)
        deck_records.append(parsed.record)

    card_lookup = collect_card_metadata(parsed_decks)
    commander_profiles = build_commander_profiles(deck_records, card_lookup)
    return DeckDataset(
        decks=tuple(deck_records),
        cards=card_lookup,
        commander_profiles=commander_profiles,
        ban_list=set(),
    )


def iter_deck_files(data_dir: Path) -> Iterator[Path]:
    """Yield deck file paths sorted for deterministic processing."""

    if not data_dir.exists():
        raise FileNotFoundError(f"Deck data directory not found: {data_dir}")

    for path in sorted(p for p in data_dir.glob('*.json') if p.is_file()):
        yield path


def parse_deck_file(path: Path) -> ParsedDeck:
    """Parse a single deck JSON file into a ``DeckRecord`` plus card metadata."""

    with path.open('r', encoding='utf-8') as handle:
        raw = json.load(handle)

    deck_data = raw.get('deck_data') or {}
    cards = deck_data.get('cards') or []

    card_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    commanders: list[str] = []
    card_ids: list[str] = []
    metadata: dict[str, CardRecord] = {}

    for entry in cards:
        card_block = entry.get('card') or {}
        oracle_block = card_block.get('oracleCard') or {}
        oracle_id = oracle_block.get('id')
        if oracle_id is None:
            continue
        oracle_id = str(oracle_id)

        quantity = int(entry.get('quantity') or 0)
        if quantity <= 0:
            continue

        categories = tuple(entry.get('categories') or ())
        is_maybeboard = 'Maybeboard' in categories
        is_commander = 'Commander' in categories

        # Build card metadata snapshot for aggregation.
        name = oracle_block.get('name') or card_block.get('name') or ''
        oracle_uid = oracle_block.get('uid')
        color_identity = tuple(oracle_block.get('colorIdentity') or ())
        super_types = list(oracle_block.get('superTypes') or ())
        card_types = list(oracle_block.get('types') or ())
        sub_types = list(oracle_block.get('subTypes') or ())
        types = tuple(t for t in [*super_types, *card_types, *sub_types] if t)
        try:
            mana_value = float(oracle_block.get('cmc') or 0.0)
        except (TypeError, ValueError):
            mana_value = 0.0
        legalities = dict(oracle_block.get('legalities') or {})
        role_tags = tuple(sorted({cat for cat in categories if cat not in {'Maybeboard', 'Commander'}}))

        metadata.setdefault(
            oracle_id,
            CardRecord(
                oracle_id=oracle_id,
                oracle_uid=oracle_uid,
                name=name,
                color_identity=color_identity,
                types=types,
                mana_value=mana_value,
                legalities=legalities,
                roles=role_tags,
            ),
        )

        if is_commander and not is_maybeboard and oracle_id not in commanders:
            commanders.append(oracle_id)

        if is_maybeboard:
            continue

        card_counts[oracle_id] += quantity
        card_ids.extend([oracle_id] * quantity)

        for cat in categories:
            if cat in {'Maybeboard', 'Commander'}:
                continue
            role_counts[cat] += quantity

    if not commanders:
        # Fallback: choose the first legendary creature in the mainboard.
        for oracle_id in card_counts:
            card = metadata.get(oracle_id)
            if not card:
                continue
            if 'Legendary' in card.types and 'Creature' in card.types:
                commanders.append(oracle_id)
                break

    color_identity = _derive_color_identity(commanders, metadata, card_counts)

    record = DeckRecord(
        deck_id=str(deck_data.get('id') or raw.get('deck_id') or path.stem),
        commanders=tuple(commanders),
        cards=tuple(card_ids),
        card_counts=dict(card_counts),
        color_identity=tuple(sorted(color_identity)),
        role_counts=dict(role_counts),
    )
    return ParsedDeck(record=record, cards=metadata)


def build_commander_profiles(
    decks: Iterable[DeckRecord],
    cards: dict[str, CardRecord],
) -> dict[str, CommanderProfile]:
    """Aggregate commander statistics needed for conditioned priors."""

    commander_counts: dict[str, Counter[str]] = defaultdict(Counter)
    commander_samples: Counter[str] = Counter()

    for deck in decks:
        deck_card_counts = deck.card_counts
        for commander in deck.commanders:
            commander_samples[commander] += 1
            commander_counts[commander].update(deck_card_counts)

    profiles: dict[str, CommanderProfile] = {}
    for commander, card_counter in commander_counts.items():
        sample_size = commander_samples[commander]
        if sample_size == 0:
            continue
        total_cards = sum(card_counter.values())
        if total_cards:
            frequencies = {
                cid: count / total_cards for cid, count in card_counter.items()
            }
        else:
            frequencies = {}

        card_record = cards.get(commander)
        color_identity = card_record.color_identity if card_record else ()
        profiles[commander] = CommanderProfile(
            oracle_id=commander,
            color_identity=color_identity,
            card_frequency=frequencies,
            sample_size=sample_size,
        )
    return profiles


def collect_card_metadata(parsed_decks: Iterable[ParsedDeck]) -> dict[str, CardRecord]:
    """Derive card metadata from parsed deck records."""

    merged: dict[str, CardRecord] = {}
    for parsed in parsed_decks:
        for oracle_id, record in parsed.cards.items():
            merged.setdefault(oracle_id, record)
    return merged


def _derive_color_identity(
    commanders: Iterable[str],
    metadata: dict[str, CardRecord],
    card_counts: Counter[str],
) -> set[str]:
    """Compute the deck color identity from commanders or the mainboard."""

    color_identity: set[str] = set()
    for commander in commanders:
        card = metadata.get(commander)
        if card:
            color_identity.update(card.color_identity)

    if color_identity:
        return color_identity

    for oracle_id in card_counts:
        card = metadata.get(oracle_id)
        if card:
            color_identity.update(card.color_identity)
    return color_identity


def load_compact_dataset(path: Path, show_progress: bool = False) -> DeckDataset:
    """Rehydrate a compact dataset JSON into ``DeckDataset`` structures."""

    # Check if file is compressed (.gz)
    if path.suffix == '.gz':
        with gzip.open(path, 'rt', encoding='utf-8') as handle:
            payload = json.load(handle)
    else:
        with path.open('r', encoding='utf-8') as handle:
            payload = json.load(handle)

    cards_data = payload.get('cards') or {}
    cards: dict[str, CardRecord] = {}
    for oracle_id, data in cards_data.items():
        cards[oracle_id] = CardRecord(
            oracle_id=oracle_id,
            oracle_uid=data.get('oracle_uid'),
            name=data.get('name') or '',
            color_identity=tuple(data.get('color_identity') or ()),
            types=tuple(data.get('types') or ()),
            mana_value=float(data.get('mana_value') or 0.0),
            legalities={'commander': 'legal' if data.get('commander_legal') else 'not_legal'},
            roles=tuple(data.get('roles') or ()),
        )

    decks_data = payload.get('decks') or []
    iterator = decks_data
    if show_progress and tqdm is not None:
        iterator = tqdm(decks_data, desc='Loading decks', unit='deck')

    deck_records: list[DeckRecord] = []
    for entry in iterator:
        card_counts = {str(cid): int(count) for cid, count in (entry.get('card_counts') or {}).items()}
        expanded_cards: list[str] = []
        for cid, count in card_counts.items():
            expanded_cards.extend([cid] * count)

        role_counts = {str(role): int(value) for role, value in (entry.get('role_counts') or {}).items()}
        deck_records.append(DeckRecord(
            deck_id=str(entry.get('deck_id') or ''),
            commanders=tuple(str(cmd) for cmd in (entry.get('commanders') or ())),
            cards=tuple(expanded_cards),
            card_counts=card_counts,
            color_identity=tuple(entry.get('color_identity') or ()),
            role_counts=role_counts,
        ))

    profiles_data = payload.get('commander_profiles') or {}
    commander_profiles: dict[str, CommanderProfile] = {}
    for commander_id, profile in profiles_data.items():
        card_frequency = {
            str(card_id): float(freq)
            for card_id, freq in (profile.get('card_frequency') or {}).items()
        }
        commander_profiles[commander_id] = CommanderProfile(
            oracle_id=commander_id,
            color_identity=tuple(profile.get('color_identity') or ()),
            card_frequency=card_frequency,
            sample_size=int(profile.get('sample_size') or 0),
        )

    return DeckDataset(
        decks=tuple(deck_records),
        cards=cards,
        commander_profiles=commander_profiles,
        ban_list=set(),
    )
