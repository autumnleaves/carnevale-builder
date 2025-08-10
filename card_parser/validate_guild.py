import json

# Load both Guild files for comparison
with open('guild_cards.json', 'r', encoding='utf-8') as f:
    original_guild = json.load(f)

with open('The_Guild_cards.json', 'r', encoding='utf-8') as f:
    new_guild = json.load(f)

print('=== Basic Statistics ===')
print(f'Original Guild cards: {len(original_guild["cards"])}')
print(f'New Guild cards: {len(new_guild["cards"])}')
print(f'Faction name - Original: "{original_guild["faction"]}"')
print(f'Faction name - New: "{new_guild["faction"]}"')

# Test the first few cards for abilities parsing
print('\n=== Capodecina Abilities Comparison (Fixed) ===')
orig_cap = original_guild['cards'][0]
new_cap = new_guild['cards'][0]

print('Original abilities:')
print(f'  Common: {orig_cap["abilities"]["common"]}')
print(f'  Unique: {[u["name"] for u in orig_cap["abilities"]["unique"]]}')
print(f'  Command: {[c["name"] for c in orig_cap["abilities"]["command"]]}')

print('\nNew (fixed) abilities:')
print(f'  Common: {new_cap["abilities"]["common"]}')
print(f'  Unique: {[u["name"] for u in new_cap["abilities"]["unique"]]}')
print(f'  Command: {[c["name"] for c in new_cap["abilities"]["command"]]}')

# Check if they match
abilities_match = (
    orig_cap['abilities']['common'] == new_cap['abilities']['common'] and
    [u['name'] for u in orig_cap['abilities']['unique']] == [u['name'] for u in new_cap['abilities']['unique']] and
    [c['name'] for c in orig_cap['abilities']['command']] == [c['name'] for c in new_cap['abilities']['command']]
)

print(f'\nCapodecina abilities match: {abilities_match}')

# Let's also check a few more cards to be thorough
print('\n=== Testing More Cards ===')
cards_to_test = min(5, len(original_guild['cards']), len(new_guild['cards']))

all_match = True
for i in range(cards_to_test):
    orig_card = original_guild['cards'][i]
    new_card = new_guild['cards'][i]
    
    card_abilities_match = (
        orig_card['abilities']['common'] == new_card['abilities']['common'] and
        [u['name'] for u in orig_card['abilities']['unique']] == [u['name'] for u in new_card['abilities']['unique']] and
        [c['name'] for c in orig_card['abilities']['command']] == [c['name'] for c in new_card['abilities']['command']]
    )
    
    print(f'{orig_card["name"]}: abilities match = {card_abilities_match}')
    if not card_abilities_match:
        all_match = False
        print(f'  Original common: {orig_card["abilities"]["common"]}')
        print(f'  New common: {new_card["abilities"]["common"]}')

print(f'\nAll tested cards match: {all_match}')
