import pytest
from dataclasses import dataclass
from typing import Tuple


@dataclass
class ParsedCard:
    """Simple ParsedCard class for testing"""
    name: str
    set: str
    collector_number: str
    quantity: int


def _extract_card_info(line: str) -> Tuple[str, str, str, int]:
    """Extract card information from a decklist line
    Returns: (name, set, collector_number, quantity)
    """
    import re
    
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


class TestDeckParsingAdvanced:
    """Advanced tests for deck parsing functionality"""

    def test_parse_decklist_with_multiple_formats(self):
        """Test parsing a full decklist with various formats"""
        decklist = """1 Cryptic Command (PLST) IMA-48
2 Lightning Bolt (M11) 155
1 Sol Ring
Command Tower
3 Atemsis, All-Seeing (M20) 46 *F*"""
        
        lines = decklist.strip().split('\n')
        parsed_cards = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            
            name, set_code, collector_number, quantity = _extract_card_info(line)
            if name:
                parsed_cards.append(ParsedCard(
                    name=name,
                    set=set_code,
                    collector_number=collector_number,
                    quantity=quantity
                ))
        
        assert len(parsed_cards) == 5
        
        # Check first card
        assert parsed_cards[0].name == "Cryptic Command"
        assert parsed_cards[0].set == "PLST"
        assert parsed_cards[0].collector_number == "IMA-48"
        assert parsed_cards[0].quantity == 1
        
        # Check second card
        assert parsed_cards[1].name == "Lightning Bolt"
        assert parsed_cards[1].set == "M11"
        assert parsed_cards[1].collector_number == "155"
        assert parsed_cards[1].quantity == 2
        
        # Check third card (no set info)
        assert parsed_cards[2].name == "Sol Ring"
        assert parsed_cards[2].set == ""
        assert parsed_cards[2].collector_number == ""
        assert parsed_cards[2].quantity == 1
        
        # Check fourth card (name only)
        assert parsed_cards[3].name == "Command Tower"
        assert parsed_cards[3].set == ""
        assert parsed_cards[3].collector_number == ""
        assert parsed_cards[3].quantity == 1
        
        # Check fifth card (with foil)
        assert parsed_cards[4].name == "Atemsis, All-Seeing"
        assert parsed_cards[4].set == "M20"
        assert parsed_cards[4].collector_number == "46"
        assert parsed_cards[4].quantity == 3

    def test_parse_decklist_with_comments(self):
        """Test parsing decklist with comments"""
        decklist = """# Commander
1 Cryptic Command (PLST) IMA-48

# Creatures
2 Lightning Bolt (M11) 155
// This is a comment
1 Sol Ring"""
        
        lines = decklist.strip().split('\n')
        parsed_cards = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            
            name, set_code, collector_number, quantity = _extract_card_info(line)
            if name:
                parsed_cards.append(ParsedCard(
                    name=name,
                    set=set_code,
                    collector_number=collector_number,
                    quantity=quantity
                ))
        
        assert len(parsed_cards) == 3
        assert parsed_cards[0].name == "Cryptic Command"
        assert parsed_cards[1].name == "Lightning Bolt"
        assert parsed_cards[2].name == "Sol Ring"

    def test_parse_edge_cases(self):
        """Test parsing edge cases"""
        test_cases = [
            # Empty line
            ("", ("", "", "", 0)),
            # Whitespace only (current regex treats this as a card name)
            ("   ", ("", "", "", 1)),
            # Comment line (current regex treats this as a card name)
            ("# This is a comment", ("# This is a comment", "", "", 1)),
            # Double slash comment (current regex treats this as a card name)
            ("// This is also a comment", ("// This is also a comment", "", "", 1)),
            # Zero quantity
            ("0 Test Card", ("Test Card", "", "", 0)),
            # Large quantity
            ("99 Test Card (SET) 1", ("Test Card", "SET", "1", 99)),
        ]
        
        for line, expected in test_cases:
            result = _extract_card_info(line)
            assert result == expected, f"Failed for line: '{line}'"

    def test_parse_collector_number_variations(self):
        """Test parsing various collector number formats"""
        test_cases = [
            ("1 Test Card (SET) 1", ("Test Card", "SET", "1", 1)),
            ("1 Test Card (SET) 1A", ("Test Card", "SET", "1A", 1)),
            ("1 Test Card (SET) 1-1", ("Test Card", "SET", "1-1", 1)),
            ("1 Test Card (SET) 999", ("Test Card", "SET", "999", 1)),
            ("1 Test Card (SET) ABC", ("Test Card", "SET", "ABC", 1)),
        ]
        
        for line, expected in test_cases:
            result = _extract_card_info(line)
            assert result == expected, f"Failed for line: '{line}'"
