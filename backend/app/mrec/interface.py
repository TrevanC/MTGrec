
"""CLI entry points for running recommendations and validation."""

from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter
from typing import Sequence

from .commanders import CommanderPriorStore
from .constraints import ConstraintChecker, DeckShapeEvaluator
from .data_ingest import load_compact_dataset, load_deck_dataset
from .deck_builder import DeckAssembler, DeckBuilderConfig
from .matrix_builder import MatrixBuilderConfig, build_matrix
from .scoring import CandidateScorer, ScoringConfig
from .similarity import CardSimilarityModel, SimilarityConfig
from .validation import ValidationConfig, run_validation


def build_argument_parser() -> argparse.ArgumentParser:
    """Return the top-level CLI argument parser."""

    parser = argparse.ArgumentParser(prog='magic-deck-rec', description='Magic deck recommendation tools')
    subparsers = parser.add_subparsers(dest='command', required=True)

    recommend_parser = subparsers.add_parser('recommend', help='Generate recommendations for an existing deck')
    recommend_parser.add_argument('--compact-path', type=Path, default=Path('data/processed/compact_dataset.json'), help='Path to compact dataset JSON (preferred)')
    recommend_parser.add_argument('--data-dir', type=Path, default=None, help='Fallback directory with raw deck JSON files')
    recommend_parser.add_argument('--deck-id', required=True, help='Deck identifier to use as the seed')
    recommend_parser.add_argument('--top', type=int, default=10, help='Number of ranked candidates to display')
    recommend_parser.add_argument('--similarity-cache', type=Path, default=None, help='Path to cache similarity neighbours')
    recommend_parser.add_argument('--refresh-cache', action='store_true', help='Rebuild similarity cache even if present')
    recommend_parser.add_argument('--verbose', action='store_true', help='Print progress while computing recommendations')

    validate_parser = subparsers.add_parser('validate', help='Run the hold-out validation harness')
    validate_parser.add_argument('--compact-path', type=Path, default=Path('data/processed/compact_dataset.json'))
    validate_parser.add_argument('--data-dir', type=Path, default=None)
    validate_parser.add_argument('--holdout-fraction', type=float, default=0.1)
    validate_parser.add_argument('--seed-size', type=int, default=60)
    validate_parser.add_argument('--precision-k', type=int, nargs='+', default=[5, 10, 20])
    validate_parser.add_argument('--similarity-cache', type=Path, default=None, help='Path to cache similarity neighbours')
    validate_parser.add_argument('--refresh-cache', action='store_true', help='Rebuild similarity cache even if present')
    validate_parser.add_argument('--verbose', action='store_true', help='Print progress while running validation')

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Program entry point for the CLI interface."""

    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.command == 'recommend':
        return _run_recommend(args)
    if args.command == 'validate':
        return _run_validate(args)
    parser.error('Unknown command')
    return 1


def _run_recommend(args: argparse.Namespace) -> int:
    total_start = perf_counter()
    verbose = getattr(args, 'verbose', False)

    if verbose:
        source = args.compact_path if args.compact_path is not None else args.data_dir
        print(f'Loading dataset from {source}...')
        step_start = perf_counter()
    else:
        step_start = total_start

    try:
        dataset = _load_dataset(args.compact_path, args.data_dir, show_progress=verbose)
    except FileNotFoundError as error:
        print(error)
        return 1

    if verbose:
        load_time = perf_counter() - step_start
        print(f'Loaded {len(dataset.decks)} decks with {len(dataset.cards)} unique cards. ({load_time:.2f}s)')
        print('Building deck-card matrix...')
        step_start = perf_counter()

    bundle = build_matrix(dataset, MatrixBuilderConfig(), verbose=verbose)

    if verbose:
        matrix_time = perf_counter() - step_start
        print(f'Matrix built with shape ({len(dataset.decks)}, {len(bundle.card_index)}) ({matrix_time:.2f}s)')

    similarity, _, _ = _build_similarity_model(
        bundle=bundle,
        cache_path=getattr(args, 'similarity_cache', None),
        refresh_cache=getattr(args, 'refresh_cache', False),
        verbose=verbose,
    )

    if verbose:
        step_start = perf_counter()

    commander_store = CommanderPriorStore(dataset.commander_profiles)
    deck_shape = DeckShapeEvaluator()
    checker = ConstraintChecker(dataset.cards, dataset.ban_list)
    scorer = CandidateScorer(
        similarity_model=similarity,
        commander_priors=commander_store,
        deck_shape=deck_shape,
        card_lookup=dataset.cards,
        global_frequencies=bundle.card_totals,
        config=ScoringConfig(),
    )
    assembler = DeckAssembler(
        constraint_checker=checker,
        deck_shape=deck_shape,
        card_lookup=dataset.cards,
        global_frequencies=bundle.card_totals,
        config=DeckBuilderConfig(ranked_list_size=args.top),
    )

    deck = _find_deck(dataset, args.deck_id)
    if deck is None:
        print(f'Deck {args.deck_id} not found in dataset')
        return 1

    scores = scorer.score_candidates(deck)

    if verbose:
        scoring_time = perf_counter() - step_start
        print(f'Generated {len(scores)} scored candidates. ({scoring_time:.2f}s)')
        print('Assembling ranked recommendations...')
        step_start = perf_counter()

    ranked = assembler.build_ranked_list(scores)

    if verbose:
        ranked_time = perf_counter() - step_start
        print(f'Ranked list ready ({ranked_time:.2f}s)')
        print('Building full deck recommendation...')
        step_start = perf_counter()

    if not ranked:
        print('No candidate recommendations available for this deck.')
    else:
        print('Top recommendations:')
        for index, (score, reason) in enumerate(ranked, start=1):
            card = dataset.cards.get(score.oracle_id)
            name = card.name if card and card.name else score.oracle_id
            print(f"{index}. {name} ({score.oracle_id}) | score={score.total:.3f}")
            print(f"   {reason.summary}")

    deck_rec = assembler.build_full_deck(deck, [score for score, _ in ranked])

    if verbose:
        deck_time = perf_counter() - step_start
        total_time = perf_counter() - total_start
        print(f'Deck assembled ({deck_time:.2f}s, total {total_time:.2f}s)')

    if deck_rec.additions:
        print()
        print('Additions suggested:', ', '.join(deck_rec.additions))
    if deck_rec.swaps:
        print()
        print('Suggested swaps:')
        for swap in deck_rec.swaps:
            out_card = dataset.cards.get(swap.outgoing)
            in_card = dataset.cards.get(swap.incoming)
            out_name = out_card.name if out_card and out_card.name else swap.outgoing
            in_name = in_card.name if in_card and in_card.name else swap.incoming
            print(f"- Replace {out_name} ({swap.outgoing}) with {in_name} ({swap.incoming}): {swap.reason.summary}")
    if deck_rec.notes:
        print()
        print('Notes:')
        for note in deck_rec.notes:
            print(f"- {note}")
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    total_start = perf_counter()
    verbose = getattr(args, 'verbose', False)

    if verbose:
        source = args.compact_path if args.compact_path is not None else args.data_dir
        print(f'Loading dataset from {source}...')
        step_start = perf_counter()
    else:
        step_start = total_start

    try:
        dataset = _load_dataset(args.compact_path, args.data_dir, show_progress=verbose)
    except FileNotFoundError as error:
        print(error)
        return 1

    if verbose:
        load_time = perf_counter() - step_start
        print(f'Loaded {len(dataset.decks)} decks with {len(dataset.cards)} unique cards. ({load_time:.2f}s)')
        print('Building deck-card matrix...')
        step_start = perf_counter()

    bundle = build_matrix(dataset, MatrixBuilderConfig(), verbose=verbose)

    if verbose:
        matrix_time = perf_counter() - step_start
        print(f'Matrix built with shape ({len(dataset.decks)}, {len(bundle.card_index)}) ({matrix_time:.2f}s)')

    similarity, _, _ = _build_similarity_model(
        bundle=bundle,
        cache_path=getattr(args, 'similarity_cache', None),
        refresh_cache=getattr(args, 'refresh_cache', False),
        verbose=verbose,
    )

    if verbose:
        step_start = perf_counter()

    commander_store = CommanderPriorStore(dataset.commander_profiles)
    deck_shape = DeckShapeEvaluator()
    scorer = CandidateScorer(
        similarity_model=similarity,
        commander_priors=commander_store,
        deck_shape=deck_shape,
        card_lookup=dataset.cards,
        global_frequencies=bundle.card_totals,
        config=ScoringConfig(),
    )

    precision_k = tuple(args.precision_k)
    validation_config = ValidationConfig(
        holdout_fraction=args.holdout_fraction,
        seed_size=args.seed_size,
        precision_k=precision_k,
    )

    if verbose:
        scorer_time = perf_counter() - step_start
        print(f'Validation scorer ready ({scorer_time:.2f}s)')
        print(f'Running validation with seed size {args.seed_size} and holdout fraction {args.holdout_fraction}...')
        step_start = perf_counter()

    result = run_validation(dataset, scorer, validation_config)

    if verbose:
        validation_time = perf_counter() - step_start
        total_time = perf_counter() - total_start
        print(f'Validation completed ({validation_time:.2f}s, total {total_time:.2f}s)')

    print('Validation metrics:')
    for k in precision_k:
        prec = result.precision.get(k, 0.0)
        rec = result.recall.get(k, 0.0)
        print(f"@{k}: precision={prec:.3f}, recall={rec:.3f}")
    print(f"Evaluated decks: {result.metadata.get('evaluated_decks', 0)}")
    return 0


def _build_similarity_model(
    bundle,
    cache_path: Path | None,
    refresh_cache: bool,
    verbose: bool,
) -> tuple[CardSimilarityModel, float, bool]:
    cache_path = Path(cache_path) if cache_path is not None else None
    start = perf_counter()

    if cache_path is not None and cache_path.exists() and not refresh_cache:
        if verbose:
            print(f'Loading similarity cache from {cache_path}...')
        try:
            model = CardSimilarityModel.load(cache_path)
            if model.is_compatible(bundle.card_index):
                elapsed = perf_counter() - start
                if verbose:
                    print(f'Using cached similarity neighbours ({elapsed:.2f}s)')
                return model, elapsed, True
            if verbose:
                print('Similarity cache is incompatible with current dataset. Recomputing...')
        except Exception as exc:
            if verbose:
                print(f'Failed to load similarity cache ({exc}). Recomputing...')

    if verbose:
        print('Computing similarity neighbours...')
        start = perf_counter()

    model = CardSimilarityModel(SimilarityConfig())
    model.fit(bundle, verbose=verbose)
    elapsed = perf_counter() - start

    if verbose:
        print(f'Computed neighbours ({elapsed:.2f}s)')

    if cache_path is not None:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            model.save(cache_path)
            if verbose:
                print(f'Saved similarity cache to {cache_path}')
        except Exception as exc:
            if verbose:
                print(f'Failed to save similarity cache ({exc})')

    return model, elapsed, False


def _load_dataset(compact_path: Path | None, data_dir: Path | None, show_progress: bool = False):
    if compact_path is not None:
        compact_path = compact_path.expanduser()
        if compact_path.exists():
            return load_compact_dataset(compact_path, show_progress=show_progress)
        print(f"Compact dataset not found at {compact_path}.", flush=True)
    if data_dir is not None:
        data_dir = data_dir.expanduser()
        if data_dir.exists():
            return load_deck_dataset(data_dir, show_progress=show_progress)
        raise FileNotFoundError(f"Raw data directory not found: {data_dir}")
    raise FileNotFoundError('No dataset source provided. Use --compact-path or --data-dir.')


def _find_deck(dataset, deck_id: str):
    for deck in dataset.decks:
        if deck.deck_id == str(deck_id):
            return deck
    return None


if __name__ == '__main__':
    raise SystemExit(main())
