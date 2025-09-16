import re
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple, Set, Optional
from app.models.card import ScryfallCard as ScryfallCardModel
from app.schemas.deck import ParsedDeck, DeckIssue, ParsedCard, DecklistCard
from app.schemas.card import ScryfallCard
from app.services.card_service import CardService

class DeckService:
    def __init__(self, db: Session):
        self.db = db
        self.card_service = CardService(db)

    async def parse_decklist(self, decklist: str, commander1: Optional[str] = None, commander2: Optional[str] = None) -> ParsedDeck:
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

        # Create decklist cards with ScryfallCard objects, combining duplicates by name
        decklist_cards = []
        card_quantities = {}  # Track quantities by card name
        
        # First pass: collect quantities for each card name
        for parsed_card in parsed_cards:
            if parsed_card.name in found_cards_map:
                if parsed_card.name not in card_quantities:
                    card_quantities[parsed_card.name] = 0
                card_quantities[parsed_card.name] += parsed_card.quantity
        
        # Second pass: create decklist cards with combined quantities
        for card_name, total_quantity in card_quantities.items():
            card = found_cards_map[card_name]
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
                quantity=total_quantity
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

        # Handle commanders from input fields
        commanders = []
        commander_names = []
        
        # Find commanders from input fields
        if commander1:
            commander_card = await self._find_card_by_name(commander1)
            if commander_card:
                commanders.append(commander_card)
                commander_names.append(commander1)
            else:
                issues.append(DeckIssue(
                    type="unknown_commander",
                    text=f"Commander not found: '{commander1}'"
                ))
        
        if commander2 and commander2.strip():
            commander_card = await self._find_card_by_name(commander2)
            if commander_card:
                commanders.append(commander_card)
                commander_names.append(commander2)
            else:
                issues.append(DeckIssue(
                    type="unknown_commander",
                    text=f"Commander not found: '{commander2}'"
                ))

        # Add commanders to decklist_cards so they appear in the decklist tab
        for commander in commanders:
            # Convert ScryfallCard model to ScryfallCard schema
            card_schema = ScryfallCard(
                id=str(getattr(commander, 'id', '')),
                oracle_id=str(getattr(commander, 'oracle_id', '')) if getattr(commander, 'oracle_id', None) else None,
                name=getattr(commander, 'name', ''),
                released_at=getattr(commander, 'released_at', None),
                set=getattr(commander, 'set', None),
                set_name=getattr(commander, 'set_name', None),
                collector_number=getattr(commander, 'collector_number', None),
                lang=getattr(commander, 'lang', None),
                cmc=getattr(commander, 'cmc', None),
                type_line=getattr(commander, 'type_line', None),
                oracle_text=getattr(commander, 'oracle_text', None),
                colors=getattr(commander, 'colors', None),
                color_identity=getattr(commander, 'color_identity', []),
                keywords=getattr(commander, 'keywords', None),
                legalities=getattr(commander, 'legalities', {}),
                image_uris=getattr(commander, 'image_uris', None),
                card_faces=getattr(commander, 'card_faces', None),
                prices=getattr(commander, 'prices', None),
                edhrec_rank=getattr(commander, 'edhrec_rank', None)
            )
            commander_decklist_card = DecklistCard(
                card=card_schema,
                quantity=1  # Commanders are always 1 copy
            )
            decklist_cards.append(commander_decklist_card)

        # All other cards are regular cards (exclude commanders)
        commander_names_set = set(commander_names)
        regular_cards = [card for card in found_cards if card.name not in commander_names_set]

        # Determine color identity
        color_identity = self._calculate_color_identity(commanders + regular_cards)

        # Validate deck composition
        composition_issues = self._validate_deck_composition(commanders, regular_cards, decklist_cards)
        issues.extend(composition_issues)

        return ParsedDeck(
            commander_ids=[str(c.id) for c in commanders],
            commander_names=commander_names,
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
            # Format: "1 Card Name (SET) NUMBER" - most common format
            r'^(\d+)x?\s+(.+?)\s+\(([^)]+)\)\s+(\d+).*$',
            # Format: "1 Card Name (SET) NUMBER *F*" (with foil)
            r'^(\d+)x?\s+(.+?)\s+\(([^)]+)\)\s+(\d+)\s*.*$',
            # Format: "1 Cryptic Command (PLST) IMA-48" (with alphanumeric collector number)
            r'^(\d+)x?\s+(.+?)\s+\(([^)]+)\)\s+([A-Z0-9\-]+).*$',
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

    async def _find_card_by_name(self, name: str) -> ScryfallCardModel:
        """Find a card by name only (case insensitive)"""
        query = self.db.query(ScryfallCardModel)
        query = query.filter(ScryfallCardModel.name.ilike(name))
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

    def _validate_deck_composition(self, commanders: List[ScryfallCardModel], regular_cards: List[ScryfallCardModel], decklist_cards: List[DecklistCard]) -> List[DeckIssue]:
        """Validate deck composition and identify issues"""
        issues = []

        # Check commander count - only validate commanders from input fields
        if len(commanders) == 0:
            issues.append(DeckIssue(
                type="missing_commander",
                text="No commander specified"
            ))
        elif len(commanders) > 2:
            issues.append(DeckIssue(
                type="too_many_commanders",
                text=f"Found {len(commanders)} commanders, maximum is 2"
            ))

        # Check deck size - count actual total cards including duplicates
        total_cards = sum(card.quantity for card in decklist_cards)
        expected_cards = 99 if len(commanders) == 1 else 98 if len(commanders) == 2 else 100
        
        if total_cards < expected_cards:
            issues.append(DeckIssue(
                type="too_few_cards",
                text=f"Deck has {total_cards} cards, should have {expected_cards}"
            ))
        elif total_cards > expected_cards:
            issues.append(DeckIssue(
                type="too_many_cards",
                text=f"Deck has {total_cards} cards, should have {expected_cards}"
            ))

        return issues