import json
import os

# Get all the faction card files
faction_files = [f for f in os.listdir('.') if f.endswith('_cards.json')]

print('=== All Faction Processing Results ===')
total_cards = 0

for faction_file in sorted(faction_files):
    with open(faction_file, 'r', encoding='utf-8') as f:
        faction_data = json.load(f)
    
    faction_name = faction_data['faction']
    card_count = len(faction_data['cards'])
    total_cards += card_count
    
    print(f'{faction_name}: {card_count} cards')
    
    # Sample one card from each faction to check abilities structure
    if card_count > 0:
        sample_card = faction_data['cards'][0]
        abilities = sample_card['abilities']
        
        common_count = len(abilities['common'])
        unique_count = len(abilities['unique'])
        command_count = len(abilities['command'])
        
        print(f'  Sample card "{sample_card["name"]}": {common_count} common, {unique_count} unique, {command_count} command abilities')
        
        # Check for the old parsing bug (concatenated abilities)
        has_concatenated = False
        for cmd_ability in abilities['command']:
            if any(common in cmd_ability['name'] for common in ['Infiltration', 'Expert Offence', 'Aerial Attack']):
                has_concatenated = True
                break
        
        if has_concatenated:
            print(f'  WARNING: Found concatenated abilities in {sample_card["name"]}')
        else:
            print(f'  ✓ Abilities properly separated')

print(f'\nTotal cards across all factions: {total_cards}')

# Let's also check a specific card from another faction to see the abilities structure
print('\n=== Sample Card from Strigoi Faction ===')
with open('Strigoi_cards.json', 'r', encoding='utf-8') as f:
    strigoi_data = json.load(f)

if strigoi_data['cards']:
    sample_strigoi = strigoi_data['cards'][0]
    print(f'Card: {sample_strigoi["name"]}')
    print(f'Common abilities: {sample_strigoi["abilities"]["common"]}')
    print(f'Unique abilities: {[u["name"] for u in sample_strigoi["abilities"]["unique"]]}')
    print(f'Command abilities: {[c["name"] for c in sample_strigoi["abilities"]["command"]]}')
