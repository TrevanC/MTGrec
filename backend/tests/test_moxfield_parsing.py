#!/usr/bin/env python3
"""Test script for Moxfield deck parsing"""

import re

def _extract_card_name(line: str) -> str:
    """Extract card name from a decklist line"""
    # Remove common prefixes like quantities
    patterns = [
        # Moxfield format: "1 Atemsis, All-Seeing (M20) 46 *F*"
        r'^\d+x?\s+(.+?)\s+\([^)]+\)\s+\d+.*$',
        # Standard formats: "1 Sol Ring" or "1x Sol Ring"
        r'^\d+x?\s+(.+)$',
        r'^(\d+)\s+(.+)$',  # "1 Sol Ring"
        r'^(.+)$',          # Just the card name
    ]

    for pattern in patterns:
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            # Get the card name (first group in the match)
            groups = match.groups()
            if groups:
                card_name = groups[0].strip()
                # Clean up common suffixes
                card_name = re.sub(r'\s*\([^)]*\)$', '', card_name)  # Remove set info like "(BRO)"
                return card_name

    return ""

# Test cases
test_cases = [
    # Moxfield format tests
    "1 Atemsis, All-Seeing (M20) 46 *F*",
    "2 Lightning Bolt (M11) 155",
    "1 Atemsis, All-Seeing (M20) 46",  # Without foil indicator
    "1 Atemsis, All-Seeing (M20) 46 *f*",  # Lowercase foil
    "3 Sol Ring (M15) 234 *F*",
    "1 Command Tower (C18) 127",
    
    # Standard format tests
    "1 Sol Ring",
    "1x Command Tower",
    "Atemsis, All-Seeing",
    "2x Lightning Bolt",
    
    # Edge cases
    "1 Jace, the Mind Sculptor (WWK) 75 *F*",
    "1 Black Lotus (LEA) 232",
    "1x Mox Pearl (LEA) 233 *F*",
]

print("Testing Moxfield deck parsing:")
print("=" * 60)

for test_line in test_cases:
    result = _extract_card_name(test_line)
    print(f"Input:  '{test_line}'")
    print(f"Output: '{result}'")
    print()

print("=" * 60)
print("Test Summary:")
print("- Moxfield format: amount cardname (setcode) setnumber *F*")
print("- Standard format: amount cardname or amountx cardname")
print("- All formats should extract just the card name")
