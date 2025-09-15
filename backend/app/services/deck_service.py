import re
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Set
from app.models.card import ScryfallCard as ScryfallCardModel
from app.schemas.deck import ParsedDeck, DeckIssue, ParsedCard, DecklistCard
from app.schemas.card import ScryfallCard
from app.services.card_service import CardService

class DeckService:
    def __init__(self, db: Session):
        self.db = db
        self.card_service = CardService(db)

    async def parse_decklist(self, decklist: str) -> ParsedDeck:
        """Parse a decklist string into structured deck data"""

        lines = decklist.strip().split('\n')
        parsed_cards = []
        issues = []

        # Parse lines to extract card information
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue

            # Try to parse card information
            name, set_code, collector_number, quantity = self._extract_card_info(line)
            if name:
                parsed_cards.append(ParsedCard(
                    name=name,
                    set=set_code,
                    collector_number=collector_number,
                    quantity=quantity
                ))
            else:
                issues.append(DeckIssue(
                    type="parse_error",
                    text=f"Line {line_num}: Could not parse '{line}'"
                ))

        if not parsed_cards:
            raise ValueError("No valid cards found in decklist")

        # Find cards in database using name, set, and collector number
        found_cards, unknown_cards = await self._resolve_parsed_cards(parsed_cards)

        # Create a mapping of found cards by name for easy lookup
        found_cards_map = {card.name: card for card in found_cards}

        # Create decklist cards with ScryfallCard objects
        decklist_cards = []
        for parsed_card in parsed_cards:
            if parsed_card.name in found_cards_map:
                card = found_cards_map[parsed_card.name]
                # Convert ScryfallCard model to ScryfallCard schema
                card_schema = ScryfallCard(
                    id=str(getattr(card, 'id', '')),
                    oracle_id=str(getattr(card, 'oracle_id', '')) if getattr(card, 'oracle_id', None) else None,
                    name=getattr(card, 'name', ''),
                    released_at=getattr(card, 'released_at', None),
                    set=getattr(card, 'set', None),
                    set_name=getattr(card, 'set_name', None),
                    collector_number=getattr(card, 'collector_number', None),
                    lang=getattr(card, 'lang', None),
                    cmc=getattr(card, 'cmc', None),
                    type_line=getattr(card, 'type_line', None),
                    oracle_text=getattr(card, 'oracle_text', None),
                    colors=getattr(card, 'colors', None),
                    color_identity=getattr(card, 'color_identity', []),
                    keywords=getattr(card, 'keywords', None),
                    legalities=getattr(card, 'legalities', {}),
                    image_uris=getattr(card, 'image_uris', None),
                    card_faces=getattr(card, 'card_faces', None),
                    prices=getattr(card, 'prices', None),
                    edhrec_rank=getattr(card, 'edhrec_rank', None)
                )
                decklist_card = DecklistCard(
                    card=card_schema,
                    quantity=parsed_card.quantity
                )
                decklist_cards.append(decklist_card)

        # Add issues for unknown cards
        for unknown_card in unknown_cards:
            suggestions = await self._find_card_suggestions(unknown_card.name)
            issues.append(DeckIssue(
                type="unknown_card",
                text=f"Card not found: '{unknown_card.name}' (Set: {unknown_card.set}, Number: {unknown_card.collector_number})",
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
            issues=issues,
            decklist=decklist_cards
        )

    def _extract_card_info(self, line: str) -> Tuple[str, str, str, int]:
        """Extract card information from a decklist line
        Returns: (name, set, collector_number, quantity)
        """
        patterns = [
            # Format: "1 Cryptic Command (PLST) IMA-48"
            r'^(\d+)x?\s+(.+?)\s+\(([^)]+)\)\s+([A-Z0-9\-]+).*$',
            # Format: "1 Cryptic Command (PLST) IMA-48 *F*" (with foil)
            r'^(\d+)x?\s+(.+?)\s+\(([^)]+)\)\s+([A-Z0-9\-]+)\s*.*$',
            # Fallback: "1 Sol Ring" (no set info)
            r'^(\d+)x?\s+(.+)$',
            r'^(\d+)\s+(.+)$',  # "1 Sol Ring"
            r'^(.+)$',          # Just the card name (quantity = 1)
        ]

        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    # Has set and collector number
                    quantity = int(groups[0])
                    name = groups[1].strip()
                    set_code = groups[2].strip()
                    collector_number = groups[3].strip()
                    return name, set_code, collector_number, quantity
                elif len(groups) == 2:
                    # Has quantity but no set info
                    quantity = int(groups[0])
                    name = groups[1].strip()
                    return name, "", "", quantity
                else:
                    # Just card name, default quantity 1
                    name = groups[0].strip()
                    return name, "", "", 1

        return "", "", "", 0

    async def _resolve_parsed_cards(self, parsed_cards: List[ParsedCard]) -> Tuple[List[ScryfallCardModel], List[ParsedCard]]:
        """Resolve parsed cards to database cards using name, set, and collector number"""
        found_cards = []
        unknown_cards = []

        for parsed_card in parsed_cards:
            card = await self._find_card_by_details(
                parsed_card.name, 
                parsed_card.set, 
                parsed_card.collector_number
            )
            if card:
                found_cards.append(card)
            else:
                unknown_cards.append(parsed_card)

        return found_cards, unknown_cards

    async def _find_card_by_details(self, name: str, set_code: str, collector_number: str) -> ScryfallCardModel:
        """Find a card by name, set, and collector number"""
        query = self.db.query(ScryfallCardModel)
        
        # Always match by name (case insensitive)
        query = query.filter(ScryfallCardModel.name.ilike(name))
        
        # If set code is provided, match by set
        if set_code:
            query = query.filter(ScryfallCardModel.set.ilike(set_code))
        
        # If collector number is provided, match by collector number
        if collector_number:
            query = query.filter(ScryfallCardModel.collector_number.ilike(collector_number))
        
        return query.first()

    async def _resolve_card_names(self, card_names: List[str]) -> Tuple[List[ScryfallCardModel], List[str]]:
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
        query = self.db.query(ScryfallCardModel.name).filter(
            ScryfallCardModel.name.ilike(f"%{card_name[:3]}%")
        ).limit(3)

        suggestions = [row[0] for row in query.all()]
        return suggestions

    def _separate_commanders(self, cards: List[ScryfallCardModel]) -> Tuple[List[ScryfallCardModel], List[ScryfallCardModel]]:
        """Separate commanders from regular cards"""
        commanders = []
        regular_cards = []

        for card in cards:
            if card.is_commander():
                commanders.append(card)
            else:
                regular_cards.append(card)

        return commanders, regular_cards

    def _calculate_color_identity(self, cards: List[ScryfallCardModel]) -> Set[str]:
        """Calculate the color identity of a list of cards"""
        color_identity = set()

        for card in cards:
            card_colors = getattr(card, 'color_identity', None)
            if card_colors:
                color_identity.update(card_colors)

        return color_identity

    def _validate_deck_composition(self, commanders: List[ScryfallCardModel], regular_cards: List[ScryfallCardModel]) -> List[DeckIssue]:
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