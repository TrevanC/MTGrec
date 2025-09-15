import re
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Set
from app.models.card import ScryfallCard
from app.schemas.deck import ParsedDeck, DeckIssue
from app.services.card_service import CardService

class DeckService:
    def __init__(self, db: Session):
        self.db = db
        self.card_service = CardService(db)

    async def parse_decklist(self, decklist: str) -> ParsedDeck:
        """Parse a decklist string into structured deck data"""

        lines = decklist.strip().split('\n')
        card_names = []
        issues = []

        # Parse lines to extract card names and quantities
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue

            # Try to parse quantity and card name
            card_name = self._extract_card_name(line)
            if card_name:
                card_names.append(card_name)
            else:
                issues.append(DeckIssue(
                    type="parse_error",
                    text=f"Line {line_num}: Could not parse '{line}'"
                ))

        if not card_names:
            raise ValueError("No valid cards found in decklist")

        # Find cards in database
        found_cards, unknown_cards = await self._resolve_card_names(card_names)

        # Add issues for unknown cards
        for unknown_card in unknown_cards:
            suggestions = await self._find_card_suggestions(unknown_card)
            issues.append(DeckIssue(
                type="unknown_card",
                text=f"Card not found: '{unknown_card}'",
                suggestions=suggestions
            ))

        # Separate commanders from other cards
        commanders, regular_cards = self._separate_commanders(found_cards)

        # Determine color identity
        color_identity = self._calculate_color_identity(commanders + regular_cards)

        # Validate deck composition
        composition_issues = self._validate_deck_composition(commanders, regular_cards)
        issues.extend(composition_issues)

        return ParsedDeck(
            commander_ids=[str(c.id) for c in commanders],
            card_ids=[str(c.id) for c in regular_cards],
            color_identity=sorted(color_identity),
            issues=issues
        )

    def _extract_card_name(self, line: str) -> str:
        """Extract card name from a decklist line"""
        # Remove common prefixes like quantities
        patterns = [
            r'^\d+x?\s+(.+)$',  # "1 Sol Ring" or "1x Sol Ring"
            r'^(\d+)\s+(.+)$',  # "1 Sol Ring"
            r'^(.+)$',          # Just the card name
        ]

        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                # Get the card name (last group in the match)
                card_name = match.groups()[-1].strip()
                # Clean up common suffixes
                card_name = re.sub(r'\s*\([^)]*\)$', '', card_name)  # Remove set info like "(BRO)"
                return card_name

        return ""

    async def _resolve_card_names(self, card_names: List[str]) -> Tuple[List[ScryfallCard], List[str]]:
        """Resolve card names to database cards"""
        found_cards = []
        unknown_cards = []

        for card_name in card_names:
            card = await self.card_service.find_card_by_name(card_name)
            if card:
                found_cards.append(card)
            else:
                unknown_cards.append(card_name)

        return found_cards, unknown_cards

    async def _find_card_suggestions(self, card_name: str) -> List[str]:
        """Find similar card names for unknown cards"""
        # Simple fuzzy matching - could be improved
        query = self.db.query(ScryfallCard.name).filter(
            ScryfallCard.name.ilike(f"%{card_name[:3]}%")
        ).limit(3)

        suggestions = [row[0] for row in query.all()]
        return suggestions

    def _separate_commanders(self, cards: List[ScryfallCard]) -> Tuple[List[ScryfallCard], List[ScryfallCard]]:
        """Separate commanders from regular cards"""
        commanders = []
        regular_cards = []

        for card in cards:
            if card.is_commander():
                commanders.append(card)
            else:
                regular_cards.append(card)

        return commanders, regular_cards

    def _calculate_color_identity(self, cards: List[ScryfallCard]) -> Set[str]:
        """Calculate the color identity of a list of cards"""
        color_identity = set()

        for card in cards:
            if card.color_identity:
                color_identity.update(card.color_identity)

        return color_identity

    def _validate_deck_composition(self, commanders: List[ScryfallCard], regular_cards: List[ScryfallCard]) -> List[DeckIssue]:
        """Validate deck composition and identify issues"""
        issues = []

        # Check commander count
        if len(commanders) == 0:
            issues.append(DeckIssue(
                type="missing_commander",
                text="No commander found in decklist"
            ))
        elif len(commanders) > 2:
            issues.append(DeckIssue(
                type="too_many_commanders",
                text=f"Found {len(commanders)} commanders, maximum is 2"
            ))

        # Check deck size
        total_cards = len(commanders) + len(regular_cards)
        if total_cards < 100:
            issues.append(DeckIssue(
                type="too_few_cards",
                text=f"Deck has {total_cards} cards, should have 100"
            ))
        elif total_cards > 100:
            issues.append(DeckIssue(
                type="too_many_cards",
                text=f"Deck has {total_cards} cards, should have 100"
            ))

        return issues