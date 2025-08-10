import re
import json
import os
from typing import Dict, List, Optional

def load_known_abilities():
    """Load the list of known common abilities and weapon abilities"""
    try:
        with open('parsed_abilities.json', 'r', encoding='utf-8') as f:
            abilities_data = json.load(f)
            return abilities_data.get('common_abilities', []), abilities_data.get('weapon_abilities', [])
    except FileNotFoundError:
        print("Warning: parsed_abilities.json not found. Using basic parsing.")
        return [], []

def normalize_description(description: str) -> str:
    """Normalize ability descriptions by replacing newlines with spaces and cleaning whitespace"""
    return re.sub(r'\s+', ' ', description).strip()

def normalize_ability_name(ability_name: str, known_abilities: List[str]) -> str:
    """Try to match an ability text to a known ability name"""
    ability_text = ability_name.strip()
    
    # Direct match
    if ability_text in known_abilities:
        return ability_text
    
    # Try to match abilities with (X) pattern - this handles cases like "Companion ( End of Days )" matching "Companion (X)"
    for known_ability in known_abilities:
        if '(X)' in known_ability:
            # Replace (X) with regex pattern to match any content in parentheses
            pattern = known_ability.replace('(X)', r'\([^)]+\)')
            if re.match(f'^{re.escape(known_ability.replace("(X)", "")).strip()}\\s*\\([^)]+\\)$', ability_text):
                return ability_text  # Return the actual ability with its specific content
    
    # Try fuzzy matching for common variations
    for known_ability in known_abilities:
        base_name = known_ability.replace('(X)', '').replace('(', '').replace(')', '').strip()
        if ability_text == base_name:
            return base_name
        # Handle abilities that might have different number formats
        if base_name in ability_text:
            return ability_text
    
    return ""  # Return empty string instead of None

def separate_concatenated_abilities(item: str, known_abilities: List[str]) -> List[str]:
    """Separate concatenated abilities using known ability names"""
    separated = []
    remaining_text = item
    
    # Sort by length (longest first) to match longer ability names first
    sorted_abilities = sorted(known_abilities, key=len, reverse=True)
    
    for known_ability in sorted_abilities:
        base_name = known_ability.replace('(X)', '').strip()
        
        # Try to find exact matches with numbers first
        number_pattern = f"{re.escape(base_name)} \\(\\d+\\)"
        match = re.search(number_pattern, remaining_text)
        if match:
            separated.append(match.group(0))
            remaining_text = remaining_text.replace(match.group(0), '', 1).strip()
            continue
        
        # Try to find abilities with (X) pattern matching any parentheses content
        if '(X)' in known_ability:
            # Create a pattern that matches the base name followed by any parentheses content
            parentheses_pattern = f"{re.escape(base_name)} \\([^)]+\\)"
            match = re.search(parentheses_pattern, remaining_text)
            if match:
                separated.append(match.group(0))
                remaining_text = remaining_text.replace(match.group(0), '', 1).strip()
                continue
        
        # Try to find base name at the beginning
        if remaining_text.startswith(base_name):
            # Check if it's followed by a capital letter (indicating another ability)
            next_pos = len(base_name)
            if (next_pos >= len(remaining_text) or 
                not remaining_text[next_pos].isalpha() or 
                remaining_text[next_pos].isupper()):
                
                separated.append(base_name)
                remaining_text = remaining_text[next_pos:].strip()
    
    # If there's still text remaining, add it
    if remaining_text:
        separated.append(remaining_text)
    
    return separated if separated else [item]

def enhanced_parse_abilities(text: str) -> Dict[str, List]:
    """Enhanced ability parsing using known abilities"""
    # Load known abilities
    known_common_abilities, _ = load_known_abilities()
    
    # Look for Character Abilities section
    abilities_pattern = r'Character Abilities\s*•?\s*(.*?)(?=\n\d+\.\d+\.\d+|$)'
    match = re.search(abilities_pattern, text, re.DOTALL)
    
    command_abilities = []
    common_abilities = []
    unique_abilities = []
    
    if match:
        abilities_text = match.group(1)
        
        # Clean the text by removing all bullet points and normalize whitespace
        cleaned_text = re.sub(r'•\s*', '', abilities_text)
        # Fix common text issues where abilities get concatenated
        cleaned_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned_text)  # Add space between lowercase-uppercase
        cleaned_text = re.sub(r'([!])([A-Z])', r'\1\n\2', cleaned_text)  # Add newline after ! before uppercase
        # Normalize whitespace but preserve line breaks after command ability headers
        cleaned_text = re.sub(r'(PULSE|AURA)\s*Command Ability\s*', r'\1 Command Ability\n', cleaned_text)
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Normalize spaces and tabs, but keep newlines
        
        # Extract command abilities
        command_pattern = r'(.*?)(PULSE|AURA)\s*Command Ability\n(.*?)(?=\n\d+\.\d+\.\d+|$)'
        command_matches = re.findall(command_pattern, cleaned_text, re.DOTALL)
        
        for match_groups in command_matches:
            pre_text = match_groups[0].strip()
            command_type = match_groups[1]
            description = match_groups[2].strip()
            
            # Clean up the description
            clean_description = normalize_description(description)
            
            # The command name should be the last meaningful line in pre_text
            lines = [line.strip() for line in pre_text.split('\n') if line.strip()]
            command_name = lines[-1] if lines else "Unknown Command"
            
            command_abilities.append({
                "name": command_name,
                "type": command_type,
                "description": clean_description
            })
        
        # Remove command abilities from text to avoid double-parsing
        text_without_commands = re.sub(r'.*?(PULSE|AURA)\s*Command Ability\s*.*?(?=\n[A-Z]|\d+\.\d+\.\d+|$)', '', cleaned_text, flags=re.DOTALL)
        
        # Parse remaining abilities
        if text_without_commands.strip():
            separated_abilities = separate_concatenated_abilities(text_without_commands, known_common_abilities)
            
            for ability_text in separated_abilities:
                ability_text = ability_text.strip()
                if not ability_text or any(x in ability_text for x in ['Actions Life Will', 'MOVEMENT DEXTERITY']):
                    continue
                
                # Check if it's a common ability
                normalized = normalize_ability_name(ability_text, known_common_abilities)
                if normalized:
                    common_abilities.append(normalized)
                else:
                    # This might be a unique ability
                    if (len(ability_text.split()) <= 8 and 
                        not re.match(r'^\s*\([^)]*\)\s*$', ability_text) and
                        ability_text != '.'):
                        
                        # Look for description in the original text
                        desc_pattern = rf'{re.escape(ability_text)}\s*(.*?)(?=\n[A-Z][a-z]|\n\d+\.\d+\.\d+|\n•|$)'
                        desc_match = re.search(desc_pattern, text, re.DOTALL)
                        description = ""
                        
                        if desc_match:
                            potential_desc = desc_match.group(1).strip()
                            if potential_desc and not any(x in potential_desc for x in ['Actions Life Will', 'MOVEMENT DEXTERITY', 'Range Evasion']):
                                description = normalize_description(potential_desc)
                        
                        unique_abilities.append({
                            "name": ability_text,
                            "description": description
                        })
    
    return {
        "common": common_abilities,
        "unique": unique_abilities,
        "command": command_abilities
    }

def parse_stats_line(stats_text: str) -> Dict[str, int]:
    """Parse the MOVEMENT DEXTERITY ATTACK PROTECTION MIND line"""
    # Look for the pattern of 5 numbers after MIND
    stats_pattern = r'MOVEMENT\s+DEXTERITY\s+ATTACK\s+PROTECTION\s+MIND\s*\n\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
    match = re.search(stats_pattern, stats_text)
    if match:
        return {
            "movement": int(match.group(1)),
            "dexterity": int(match.group(2)),
            "attack": int(match.group(3)),
            "protection": int(match.group(4)),
            "mind": int(match.group(5))
        }
    
    # Fallback - find any sequence of 5 numbers after the headers
    numbers = re.findall(r'\d+', stats_text)
    if len(numbers) >= 5:
        # Take the last 5 numbers as they're most likely the stats
        stats_numbers = numbers[-5:]
        return {
            "movement": int(stats_numbers[0]),
            "dexterity": int(stats_numbers[1]),
            "attack": int(stats_numbers[2]),
            "protection": int(stats_numbers[3]),
            "mind": int(stats_numbers[4])
        }
    return {}

def parse_weapons(text: str) -> List[Dict]:
    """Parse weapon information from the text"""
    weapons = []
    
    # Look for weapon section pattern
    weapon_section_pattern = r'Weapon Range Evasion Damage Penetration Abilities\n(.*?)(?=MOVEMENT DEXTERITY ATTACK PROTECTION MIND|Keywords)'
    match = re.search(weapon_section_pattern, text, re.DOTALL)
    
    if match:
        weapon_text = match.group(1).strip()
        weapon_lines = weapon_text.split('\n')
        
        for line in weapon_lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for weapon pattern: Name Range Evasion Damage Penetration Abilities
            weapon_match = re.match(r'^([^"]+)\s+(\d+"|-)?\s*([+-]?\d+|-)?\s*([+-]?\d+|-)?\s*([+-]?\d+|-)?\s*(.*?)$', line)
            
            if weapon_match:
                name, range_val, evasion, damage, penetration, abilities = weapon_match.groups()
                
                # Clean up weapon name
                name = name.strip()
                if not name:
                    continue
                
                # Validate this looks like a weapon
                if range_val or (evasion and evasion != '-') or (damage and damage != '-'):
                    weapon = {
                        "name": name,
                        "range": range_val if range_val and range_val != '-' else '0"',
                        "evasion": evasion if evasion and evasion != '-' else '0',
                        "damage": damage if damage and damage != '-' else '0',
                        "penetration": penetration if penetration and penetration != '-' else '0',
                        "abilities": abilities.strip() if abilities else ""
                    }
                    weapons.append(weapon)
    
    return weapons

def parse_keywords_and_rank(text: str) -> tuple[List[str], Optional[str]]:
    """Extract keywords and rank from the text"""
    keywords = []
    rank = None
    
    # Look for the Keywords section
    keyword_pattern = r'Keywords\s*•\s*(.*?)(?=Character Abilities)'
    match = re.search(keyword_pattern, text, re.DOTALL)
    
    if match:
        keyword_text = match.group(1)
        
        # Handle Discipline keywords specially
        discipline_pattern = r'Discipline\s*\(\s*([^)]*(?:\n[^)•]*)*)\s*\)'
        discipline_matches = re.findall(discipline_pattern, keyword_text, re.DOTALL)
        
        # Remove discipline patterns from keyword text
        keyword_text_clean = re.sub(discipline_pattern, '', keyword_text, flags=re.DOTALL)
        
        # Process discipline keywords
        for discipline_content in discipline_matches:
            clean_disciplines = re.sub(r'\s+', ' ', discipline_content.replace('\n', ' ')).strip()
            clean_disciplines = clean_disciplines.rstrip(',').strip()
            keywords.append(f"Discipline ( {clean_disciplines} )")
        
        # Process remaining keywords
        keyword_items = re.split(r'•', keyword_text_clean)
        for item in keyword_items:
            item = item.strip()
            if item and not item.startswith('Character Abilities'):
                item = re.sub(r'\s+', ' ', item).strip()
                
                if len(item) <= 2:
                    continue
                
                # Check if this is a rank
                if any(rank_word in item for rank_word in ["Leader", "Hero", "Henchman"]):
                    rank = item.strip()
                elif "Faction" not in item and item:
                    clean_item = re.sub(r'\([^)]*\)', '', item).strip()
                    if clean_item:
                        keywords.append(clean_item)
    
    return keywords, rank

def parse_faction_ability(text: str, faction_name: str) -> Dict:
    """Parse faction ability from page 1 text"""
    faction_ability = {}
    
    # Look for PULSE Command Ability pattern
    faction_match = re.search(r'([^\n]*?)\s*PULSE Command Ability\s*(.*)', text, re.DOTALL)
    if faction_match:
        # The ability name is usually the last meaningful line before "PULSE Command Ability"
        pre_text = faction_match.group(1)
        description = faction_match.group(2).strip()
        
        # Extract ability name from pre_text
        lines = [line.strip() for line in pre_text.split('\n') if line.strip()]
        ability_name = "Unknown Ability"
        
        # Look for the ability name (usually appears after faction keyword info)
        for i, line in enumerate(lines):
            if not any(x in line.lower() for x in ['faction', 'keyword', 'may use', 'command ability']):
                if len(line.split()) <= 6 and not line.startswith('Any'):  # Reasonable ability name length
                    ability_name = line
                    break
        
        # Clean up the description
        description = re.sub(r'\s+', ' ', description).strip()
        
        faction_ability = {
            "name": ability_name,
            "description": description
        }
    
    return faction_ability

def parse_card_universal(card_text: str, page_num: int) -> Dict:
    """Universal card parser that works for all factions"""
    lines = card_text.strip().split('\n')
    card_data = {}
    
    # Find the character name - it's usually the last non-empty line of the page
    name = None
    for line in reversed(lines):
        line = line.strip()
        if line and len(line) < 50:  # Reasonable name length
            name = line
            break
    
    if not name:
        return {"error": "No character name found", "page": page_num}
    
    card_data["name"] = name
    card_data["page"] = page_num
    
    # Parse keywords and rank
    keywords, rank = parse_keywords_and_rank(card_text)
    card_data["keywords"] = keywords
    card_data["rank"] = rank
    
    # Parse Actions Life Will Command - handle different header orders
    has_command = any(x in card_text for x in ["Actions Life Will Command", "Actions Life Command", "Command Will"])
    has_will = "Will" in card_text
    
    # Find the version and stats pattern
    stats_pattern = r'(\d+\.\d+\.\d+)\s*\n\s*(\d+(?:\s+\d+)?)\s*\n\s*(\d{2,6})'
    stats_match = re.search(stats_pattern, card_text)
    
    if stats_match:
        card_data["version"] = stats_match.group(1)
        stats_string = stats_match.group(3)
        
        # Parse based on presence of command and will
        if has_command and len(stats_string) >= 4:
            card_data["actions"] = int(stats_string[0])
            card_data["command"] = int(stats_string[-1])
            
            if has_will and len(stats_string) >= 3:
                card_data["will"] = int(stats_string[-2])
                card_data["life"] = int(stats_string[1:-2]) if len(stats_string) > 3 else 0
            else:
                card_data["life"] = int(stats_string[1:-1])
                card_data["will"] = 0
        
        elif not has_command and len(stats_string) >= 2:
            card_data["actions"] = int(stats_string[0])
            
            if has_will and len(stats_string) >= 3:
                card_data["will"] = int(stats_string[-1])
                card_data["life"] = int(stats_string[1:-1])
            else:
                card_data["life"] = int(stats_string[1:])
                card_data["will"] = 0
            
            card_data["command"] = None
    else:
        # Default values
        card_data["version"] = "2.2.0"
        card_data["actions"] = 0
        card_data["life"] = 0
        card_data["will"] = 0
        card_data["command"] = None
    
    # Parse Ducats and Base Size
    end_pattern = r'\d+\.\d+\.\d+\s*\n(\d+(?:\s+\d+)?)\s*\n\s*\d{2,6}\s*\n.*?[A-Za-z]'
    end_match = re.search(end_pattern, card_text, re.MULTILINE | re.DOTALL)
    
    if end_match:
        number_string = end_match.group(1).strip()
        
        if ' ' in number_string:
            parts = number_string.split()
            if len(parts) == 2:
                card_data["base_size"] = int(parts[0])
                card_data["ducats"] = int(parts[1])
            else:
                card_data["ducats"] = 0
                card_data["base_size"] = 0
        elif len(number_string) == 4:
            card_data["base_size"] = int(number_string[:2])
            card_data["ducats"] = int(number_string[2:])
        else:
            card_data["ducats"] = 0
            card_data["base_size"] = 0
    else:
        card_data["ducats"] = 0
        card_data["base_size"] = 0
    
    # Parse stat block
    card_data["stat_block"] = parse_stats_line(card_text)
    
    # Parse weapons
    card_data["weapons"] = parse_weapons(card_text)
    
    # Parse abilities
    card_data["abilities"] = enhanced_parse_abilities(card_text)
    
    return card_data

def parse_faction_cards(faction_name: str, extracted_text_file: str) -> Dict:
    """Parse all cards for a given faction"""
    with open(extracted_text_file, "r", encoding="utf-8") as f:
        pages = json.load(f)
    
    cards = []
    faction_ability = {}
    
    for page in pages:
        page_num = page["page"]
        text = page["text"]
        
        # Extract faction ability from first page
        if page_num == 1:
            faction_ability = parse_faction_ability(text, faction_name)
            continue  # Skip first page for card parsing
        
        # Parse individual character cards
        card = parse_card_universal(text, page_num)
        if card and card.get("name") and not card.get("error"):
            cards.append(card)
    
    return {
        "faction": faction_name,
        "faction_ability": faction_ability,
        "cards": cards
    }

if __name__ == "__main__":
    # Process all factions
    with open('extraction_summary.json', 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    results = {}
    
    for faction_name, info in summary.items():
        print(f"Processing {faction_name}...")
        
        # Parse cards for this faction
        faction_data = parse_faction_cards(faction_name, info['text_file'])
        
        # Save to faction-specific JSON file
        output_file = f"{faction_name.lower()}_cards.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(faction_data, f, indent=2, ensure_ascii=False)
        
        print(f"  Parsed {len(faction_data['cards'])} cards")
        print(f"  Saved to {output_file}")
        
        results[faction_name] = {
            "cards_parsed": len(faction_data['cards']),
            "output_file": output_file,
            "faction_ability": faction_data['faction_ability'].get('name', 'Unknown')
        }
    
    # Save processing summary
    with open('parsing_summary.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nParsing complete! Processed {len(results)} factions.")
    print("Summary saved to parsing_summary.json")
