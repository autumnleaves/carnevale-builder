#!/usr/bin/env python3
"""
Test the enhanced name extraction
"""
import sys
sys.path.append('.')
from parse_cards import extract_character_name

# Page 15 lines
lines = [
    'Actions Life Will Ducats Size',
    'MOVEMENT DEXTERITY ATTACK PROTECTION MIND',
    '5 4 3 2 1',
    'Keywords',
    '• Faction (The Doctors)',
    '• Hero',
    'Character Abilities',
    '• Concealment (2)',
    '• First Strike (2)Stride Through The Void - 1AP',
    'This character gains Ethereal  until ',
    'the end of its turn.',
    '2.2.0',
    '3013',
    ' 2112',
    'Weapon Range Evasion Damage Penetration Abilities',
    'Poisoned Needle 0" - - -1 Poisoned Ethereal Assassin'
]

name = extract_character_name(lines)
print(f"Extracted name: '{name}'")

# Test page 16 too
lines16 = [
    'Actions Life Will Ducats Size',
    'MOVEMENT DEXTERITY ATTACK PROTECTION MIND',
    '4 4 3 4 1',
    'Keywords',
    '• Faction (The Doctors)',
    '• Hero',
    'Character Abilities',
    '• Engage',
    '• Expert Grappler (2)Stride Through The Void - 1AP',
    'This character gains Ethereal  until ',
    'the end of its turn.',
    'Drag Through The Void',
    'Targets of this characters Grapple  ',
    'actions may be moved as if they had ',
    'the Ethereal  special rule.',
    '2.2.0',
    '4015',
    ' 2142',
    'Weapon Range Evasion Damage Penetration Abilities',
    'Electro Gauntlet 0" - - -2 Stun Ethereal Snatcher'
]

name16 = extract_character_name(lines16)
print(f"Page 16 extracted name: '{name16}'")
