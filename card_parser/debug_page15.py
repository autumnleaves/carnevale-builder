#!/usr/bin/env python3
"""
Debug script to understand why page 15 is not being parsed correctly.
"""
import json
import sys

def debug_page_15():
    # Load the extracted text
    with open('The_Doctors_extracted_text.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Find page 15
    page_15_data = None
    for entry in data:
        if entry['page'] == 15:
            page_15_data = entry
            break
    
    if not page_15_data:
        print("Page 15 not found!")
        return
    
    text = page_15_data['text']
    lines = text.strip().split('\n')
    
    print("=== PAGE 15 DEBUG ===")
    print("Raw text:")
    print(text)
    print("\n=== LINES ===")
    for i, line in enumerate(lines):
        print(f"{i:2}: '{line}'")
    
    # Find the character name using current logic - it's the last non-empty line
    name = None
    print("\n=== NAME DETECTION ===")
    for i, line in enumerate(reversed(lines)):
        line = line.strip()
        print(f"Checking line (reversed {i}): '{line}'")
        if line:  # Take the first (last in order) non-empty line
            name = line
            print(f"Found name: '{name}'")
            break
    
    print(f"\nFinal name: '{name}'")
    
    # Check if this looks like a weapon line
    weapon_pattern = r'^(.+?)\s+(\d+["\']?)\s+([\+\-]?\d*)\s+([\+\-]?\d*)\s+([\+\-]?\d*)\s+(.*)$'
    import re
    if re.match(weapon_pattern, name or ''):
        print("This looks like a weapon line, not a card name!")
    
    # Let's see what would be a better card name
    print("\n=== POTENTIAL CARD NAMES ===")
    for line in lines:
        line = line.strip()
        if line and not any(x in line for x in ['Actions', 'MOVEMENT', 'Weapon', '•', 'Keywords', 'Character Abilities', 'PULSE', 'AURA']):
            if len(line.split()) <= 4:  # Reasonable card name length
                print(f"Potential name: '{line}'")

if __name__ == "__main__":
    debug_page_15()
