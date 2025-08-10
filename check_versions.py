#!/usr/bin/env python3
import json

try:
    with open('guild_cards.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_cards = len(data['cards'])
    cards_with_version = sum(1 for card in data['cards'] if 'version' in card)
    
    print(f"Total cards: {total_cards}")
    print(f"Cards with version: {cards_with_version}")
    
    if cards_with_version != total_cards:
        print("Cards missing version:")
        for card in data['cards']:
            if 'version' not in card:
                print(f"  - {card['name']}")
    
    # Show version distribution
    versions = {}
    for card in data['cards']:
        if 'version' in card:
            version = card['version']
            versions[version] = versions.get(version, 0) + 1
    
    print("\nVersion distribution:")
    for version, count in sorted(versions.items()):
        print(f"  {version}: {count} cards")
        
except Exception as e:
    print(f"Error: {e}")
