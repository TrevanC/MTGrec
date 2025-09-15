import pytest
import re
from typing import Tuple


def _extract_card_info(line: str) -> Tuple[str, str, str, int]:
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


class TestDeckParsing:
    """Test cases for deck parsing functionality"""

    def test_parse_card_with_set_and_collector_number(self):
        """Test parsing cards with full set information"""
        line = "1 Cryptic Command (PLST) IMA-48"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Cryptic Command"
        assert set_code == "PLST"
        assert collector_number == "IMA-48"
        assert quantity == 1

    def test_parse_card_with_foil_indicator(self):
        """Test parsing cards with foil indicators"""
        line = "1 Atemsis, All-Seeing (M20) 46 *F*"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Atemsis, All-Seeing"
        assert set_code == "M20"
        assert collector_number == "46"
        assert quantity == 1

    def test_parse_card_with_x_notation(self):
        """Test parsing cards with 'x' notation"""
        line = "2x Lightning Bolt (M11) 155"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Lightning Bolt"
        assert set_code == "M11"
        assert collector_number == "155"
        assert quantity == 2

    def test_parse_card_without_set_info(self):
        """Test parsing cards without set information"""
        line = "1 Sol Ring"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Sol Ring"
        assert set_code == ""
        assert collector_number == ""
        assert quantity == 1

    def test_parse_card_name_only(self):
        """Test parsing cards with just the name"""
        line = "Command Tower"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Command Tower"
        assert set_code == ""
        assert collector_number == ""
        assert quantity == 1

    def test_parse_multiple_copies(self):
        """Test parsing cards with multiple copies"""
        line = "3 Sol Ring (M15) 234"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Sol Ring"
        assert set_code == "M15"
        assert collector_number == "234"
        assert quantity == 3

    def test_parse_complex_card_name(self):
        """Test parsing cards with complex names"""
        line = "2x Jace, the Mind Sculptor (WWK) 75 *F*"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Jace, the Mind Sculptor"
        assert set_code == "WWK"
        assert collector_number == "75"
        assert quantity == 2

    def test_parse_legacy_cards(self):
        """Test parsing legacy cards"""
        line = "1 Black Lotus (LEA) 232"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Black Lotus"
        assert set_code == "LEA"
        assert collector_number == "232"
        assert quantity == 1

    def test_parse_card_with_hyphenated_collector_number(self):
        """Test parsing cards with hyphenated collector numbers"""
        line = "1x Mox Pearl (LEA) 233"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "Mox Pearl"
        assert set_code == "LEA"
        assert collector_number == "233"
        assert quantity == 1

    def test_parse_invalid_line(self):
        """Test parsing invalid lines"""
        line = "invalid line format"
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == "invalid line format"
        assert set_code == ""
        assert collector_number == ""
        assert quantity == 1

    def test_parse_empty_line(self):
        """Test parsing empty lines"""
        line = ""
        name, set_code, collector_number, quantity = _extract_card_info(line)
        
        assert name == ""
        assert set_code == ""
        assert collector_number == ""
        assert quantity == 0

    @pytest.mark.parametrize("line,expected", [
        ("1 Cryptic Command (PLST) IMA-48", ("Cryptic Command", "PLST", "IMA-48", 1)),
        ("2 Lightning Bolt (M11) 155", ("Lightning Bolt", "M11", "155", 2)),
        ("1 Atemsis, All-Seeing (M20) 46 *F*", ("Atemsis, All-Seeing", "M20", "46", 1)),
        ("3 Sol Ring (M15) 234", ("Sol Ring", "M15", "234", 3)),
        ("1 Command Tower", ("Command Tower", "", "", 1)),
        ("2x Jace, the Mind Sculptor (WWK) 75 *F*", ("Jace, the Mind Sculptor", "WWK", "75", 2)),
        ("1 Black Lotus (LEA) 232", ("Black Lotus", "LEA", "232", 1)),
        ("1x Mox Pearl (LEA) 233", ("Mox Pearl", "LEA", "233", 1)),
    ])
    def test_parse_card_parametrized(self, line, expected):
        """Parametrized test for various card formats"""
        result = _extract_card_info(line)
        assert result == expected
