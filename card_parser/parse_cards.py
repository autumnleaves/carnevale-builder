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

import json
import re
from typing import Dict, List

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
            # This handles both numbers and text like "End of Days", "Trade", etc.
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

def parse_outside_unique_abilities(text: str, known_common_abilities: List[str]) -> List[Dict]:
    """Parse unique abilities that appear outside the Character Abilities section"""
    unique_abilities = []
    
    # Look for unique abilities that appear outside Character Abilities section
    # These typically appear between stat block and Keywords section
    outside_abilities_pattern = r'MIND\s*\n\s*\d+\s+\d+\s+\d+\s+\d+\s+\d+\s*\n(.*?)(?=Keywords|Character Abilities)'
    outside_match = re.search(outside_abilities_pattern, text, re.DOTALL)
    
    if outside_match:
        outside_text = outside_match.group(1).strip()
        if outside_text:
            # Look for ability names followed by descriptions
            # Pattern: Single line ability name, then multi-line description
            # Split on lines that start with a capital letter and don't contain common words
            lines = outside_text.split('\n')
            current_ability = None
            current_description_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line looks like an ability name (short, title case)
                # vs description text (longer, contains common words like "friendly", "character", etc.)
                is_ability_name = (
                    len(line.split()) <= 3 and  # Short line
                    len(line) > 2 and  # Must be longer than just punctuation
                    line[0].isupper() and  # Starts with capital
                    not any(word in line.lower() for word in ['friendly', 'character', 'gain', 'until', 'keyword', 'instead', 'add', 'when', 'may']) and  # Not description text
                    not line.endswith('.') and  # Real ability names shouldn't end with periods
                    not re.match(r'^[A-Z][a-z]* \(\d+\)\.$', line) and  # Don't match things like "Swimmer (2)."
                    line != '.'  # Simply reject any ability name that is just a period
                )
                
                if is_ability_name:
                    # Save previous ability if we have one
                    if current_ability:
                        description = normalize_description('\n'.join(current_description_lines))
                        # Check if it's not a common ability
                        normalized = normalize_ability_name(current_ability, known_common_abilities)
                        if not normalized and current_ability != '.':  # Extra check: don't add periods as abilities
                            unique_abilities.append({
                                "name": current_ability,
                                "description": description
                            })
                    
                    # Start new ability
                    current_ability = line
                    current_description_lines = []
                else:
                    # This is part of the description
                    if current_ability:  # Only add if we have an ability name
                        current_description_lines.append(line)
            
            # Don't forget the last ability
            if current_ability:
                description = normalize_description('\n'.join(current_description_lines))
                normalized = normalize_ability_name(current_ability, known_common_abilities)
                if not normalized and current_ability != '.':  # Extra check: don't add periods as abilities
                    unique_abilities.append({
                        "name": current_ability,
                        "description": description
                    })
    
    return unique_abilities


def parse_command_abilities(cleaned_text: str, known_common_abilities: List[str]) -> tuple[List[Dict], List[str]]:
    """Parse command abilities and return them along with any common abilities found in the process"""
    command_abilities = []
    common_abilities = []
    
    # Extract all command abilities with their descriptions
    command_pattern = r'(.*?)(PULSE|AURA)\s*Command Ability\n(.*?)(?=\n\d+\.\d+\.\d+|$)'
    command_matches = re.findall(command_pattern, cleaned_text, re.DOTALL)
    
    for match_groups in command_matches:
        pre_text = match_groups[0].strip()
        command_type = match_groups[1]
        description = match_groups[2].strip()
        
        # Clean up the description - remove extra newlines and normalize spaces
        clean_description = normalize_description(description)
        
        # Parse the pre_text line by line to extract common abilities and the command name
        lines = [line.strip() for line in pre_text.split('\n') if line.strip()]
        found_commons = []
        command_name = ""
        
        for line in lines:
            # First, try to separate any concatenated abilities in this line
            separated_line_abilities = separate_concatenated_abilities(line, known_common_abilities)
            
            # Process each separated ability
            for ability_text in separated_line_abilities:
                ability_text = ability_text.strip()
                if not ability_text:
                    continue
                    
                # Try to match against known common abilities
                normalized = normalize_ability_name(ability_text, known_common_abilities)
                if normalized:
                    if normalized not in found_commons:
                        found_commons.append(normalized)
                else:
                    # This is not a common ability, it might be the command name
                    if not command_name:  # Take the first non-common ability as the command name
                        command_name = ability_text
        
        # Add found common abilities
        common_abilities.extend(found_commons)
        
        # The command name should be the last non-common ability line
        if not command_name and lines:
            command_name = lines[-1]  # Fallback to last line
        
        if command_name:
            command_abilities.append({
                "name": command_name,
                "type": command_type,
                "description": clean_description
            })
    
    return command_abilities, common_abilities


def parse_remaining_abilities(cleaned_text: str, known_common_abilities: List[str], original_text: str) -> tuple[List[str], List[Dict]]:
    """Parse remaining common and unique abilities after command abilities are removed"""
    common_abilities = []
    unique_abilities = []
    
    # Remove command abilities from the text to avoid double-parsing
    text_without_commands = re.sub(r'.*?(PULSE|AURA)\s*Command Ability\s*.*?(?=\n[A-Z]|\d+\.\d+\.\d+|$)', '', cleaned_text, flags=re.DOTALL)
    
    # Parse remaining abilities by separating concatenated ones
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
            # This might be a unique ability - extract its description from original text
            if (len(ability_text.split()) <= 8 and 
                not re.match(r'^\s*\([^)]*\)\s*$', ability_text)):
                
                # Look for description in the original text
                desc_pattern = rf'{re.escape(ability_text)}\s*(.*?)(?=\n[A-Z][a-z]|\n\d+\.\d+\.\d+|\n•|$)'
                desc_match = re.search(desc_pattern, original_text, re.DOTALL)
                description = ""
                
                if desc_match:
                    potential_desc = desc_match.group(1).strip()
                    # Only use as description if it's not just stats or other card data
                    if potential_desc and not any(x in potential_desc for x in ['Actions Life Will', 'MOVEMENT DEXTERITY', 'Range Evasion', 'PULSE Command', 'AURA Command']):
                        description = normalize_description(potential_desc)
                
                if ability_text != '.' and not ability_text.endswith(' .'):  # Don't add periods as abilities or text ending with " ."
                    unique_abilities.append({
                        "name": ability_text,
                        "description": description
                    })
    
    return common_abilities, unique_abilities


def enhanced_parse_abilities(text: str) -> Dict[str, List]:
    """Enhanced ability parsing using known abilities - refactored into separate functions"""
    # Load known abilities
    known_common_abilities, _ = load_known_abilities()
    
    # Parse unique abilities that appear outside Character Abilities section
    outside_unique_abilities = parse_outside_unique_abilities(text, known_common_abilities)
    
    # Look for Character Abilities section
    abilities_pattern = r'Character Abilities\s*•?\s*(.*?)(?=\n\d+\.\d+\.\d+|$)'
    match = re.search(abilities_pattern, text, re.DOTALL)
    
    command_abilities = []
    common_abilities = []
    character_section_unique_abilities = []
    
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
        
        # Parse command abilities and any common abilities found in the process
        command_abilities, command_common_abilities = parse_command_abilities(cleaned_text, known_common_abilities)
        common_abilities.extend(command_common_abilities)
        
        # Parse remaining abilities (common and unique) after command abilities are removed
        remaining_common_abilities, character_section_unique_abilities = parse_remaining_abilities(cleaned_text, known_common_abilities, text)
        common_abilities.extend(remaining_common_abilities)
    
    # Combine all unique abilities
    all_unique_abilities = outside_unique_abilities + character_section_unique_abilities
    
    return {
        "common": common_abilities,
        "unique": all_unique_abilities,
        "command": command_abilities
    }

# The rest of the functions remain the same as the working parser

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
            
            # Normalize hyphenated discipline names
            clean_disciplines = clean_disciplines.replace('Fateweav - ing', 'Fateweaving')
            clean_disciplines = clean_disciplines.replace('Runes of Sover - eignty', 'Runes of Sovereignty')
            clean_disciplines = clean_disciplines.replace('Blood Ri - tes', 'Blood Rites')
            clean_disciplines = clean_disciplines.replace('Wild Ma - gic', 'Wild Magic')
            
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

# Continue with the original working card parsing logic but use enhanced ability parsing
def parse_card_enhanced(card_text: str, page_num: int) -> Dict:
    """Parse a single card with enhanced ability parsing"""
    lines = card_text.strip().split('\n')
    card_data = {}
    
    # Find the character name - it's the last non-empty line of the page
    name = None
    for line in reversed(lines):
        line = line.strip()
        if line:  # Take the first (last in order) non-empty line
            name = line
            break
    
    if not name:
        return {"error": "No character name found", "page": page_num, "text_sample": card_text[:200]}
    
    card_data["name"] = name
    
    card_data["page"] = page_num
    
    # Parse keywords and rank
    keywords, rank = parse_keywords_and_rank(card_text)
    card_data["keywords"] = keywords
    card_data["rank"] = rank
    
    # Parse Actions Life Will Command - look for the encoded number
    # Check if this character has Command ability (Leaders/Heroes usually do)
    has_command = "Actions Life Will Command" in card_text
    
    # Check if Will is in the header (right after Life)
    has_will = "Life Will" in card_text
    
    # Find the encoded stats number (usually 2-5 digits after version number)
    # Some cards have spaces in numbers like "30 6" instead of "306"
    # Some simple cards like Dog only have 2 digits (actions + life)
    stats_pattern = r'(\d+\.\d+\.\d+)\s*\n\s*(\d+(?:\s+\d+)?)\s*\n\s*(\d{2,5})'
    stats_match = re.search(stats_pattern, card_text)
    
    if stats_match:
        card_data["version"] = stats_match.group(1)  # Extract version number
        stats_string = stats_match.group(3)  # The longer number contains the stats
        
        if has_command and len(stats_string) >= 4:
            # Format: Actions(1), Life(variable), Will(1 or nothing), Command(last)
            card_data["actions"] = int(stats_string[0])
            card_data["command"] = int(stats_string[-1])  # Last digit is always command
            
            # Check if Will is present (second to last digit)
            if has_will and len(stats_string) >= 3:
                card_data["will"] = int(stats_string[-2])  # Second to last is will
                # Life is everything between actions and will
                if len(stats_string) > 3:
                    card_data["life"] = int(stats_string[1:-2])
                else:
                    card_data["life"] = 0  # Edge case
            else:
                # No will, life is everything between actions and command
                card_data["life"] = int(stats_string[1:-1])
                card_data["will"] = 0
        
        elif not has_command and len(stats_string) >= 2:
            # Format for non-command characters: Actions(1), Life(variable), Will(1 or nothing)
            card_data["actions"] = int(stats_string[0])
            
            # Check if Will is present
            if has_will and len(stats_string) >= 3:
                card_data["will"] = int(stats_string[-1])  # Last digit is will
                # Life is everything between actions and will
                card_data["life"] = int(stats_string[1:-1])
            else:
                # No will, life is everything after actions
                card_data["life"] = int(stats_string[1:])
                card_data["will"] = 0
            
            card_data["command"] = None
    else:
        card_data["version"] = "2.2.0"  # Default version when not found
        card_data["actions"] = 0
        card_data["life"] = 0
        card_data["will"] = 0
        card_data["command"] = None
    
    # Parse Ducats and Base Size from the structured end pattern
    # Pattern: version number, base size/ducats, stats block, then eventually the card name
    # Base size/ducats can be "3010" (30 base, 10 ducats) or "30 8" (30 base, 8 ducats)
    # Stats block can vary in length (2-6 digits) - some cards like Dog only have 2 digits
    # There might be other text between stats block and name
    end_pattern = r'\d+\.\d+\.\d+\s*\n(\d+(?:\s+\d+)?)\s*\n\s*\d{2,6}\s*\n.*?[A-Za-z]'
    end_match = re.search(end_pattern, card_text, re.MULTILINE | re.DOTALL)
    
    if end_match:
        number_string = end_match.group(1).strip()  # The base size/ducats number
        
        # Handle spaced format like "30 8" (base size, ducats)
        if ' ' in number_string:
            parts = number_string.split()
            if len(parts) == 2:
                card_data["base_size"] = int(parts[0])  # First number is base size
                card_data["ducats"] = int(parts[1])     # Second number is ducats
            else:
                card_data["ducats"] = 0
                card_data["base_size"] = 0
        # Handle 4-digit format like "3010" (base size + ducats combined)
        elif len(number_string) == 4:
            card_data["base_size"] = int(number_string[:2])  # First two digits
            card_data["ducats"] = int(number_string[2:])     # Last two digits
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
    
    # Use enhanced ability parsing
    card_data["abilities"] = enhanced_parse_abilities(card_text)
    
    # Command was already parsed above in the ALW section
    
    return card_data

# Main parsing function
def parse_all_cards_enhanced():
    """Parse all cards with enhanced ability parsing"""
    with open("extracted_text.json", "r", encoding="utf-8") as f:
        pages = json.load(f)
    
    cards = []
    faction_ability = {}
    
    for page in pages:
        page_num = page["page"]
        text = page["text"]
        
        # Extract faction ability from first page
        if page_num == 1 and "Mob Mentality" in text:
            # Extract everything after "PULSE Command Ability" until end
            faction_match = re.search(r'Mob Mentality\s*PULSE Command Ability\s*(.*)', text, re.DOTALL)
            if faction_match:
                description = faction_match.group(1).strip()
                # Clean up the description
                description = re.sub(r'\s+', ' ', description).strip()
                faction_ability = {
                    "name": "Mob Mentality",
                    "description": description
                }
        
        # Skip the first page as it only contains faction ability
        if page_num == 1:
            continue
            
        # Try to parse as individual character cards
        card = parse_card_enhanced(text, page_num)
        if card and card.get("name") and len(card["name"]) < 50:  # Reasonable name length
            cards.append(card)
    
    return {
        "faction": "The Guild",
        "faction_ability": faction_ability,
        "cards": cards
    }

if __name__ == "__main__":
    print("Loading text from extracted_text.json")
    
    result = parse_all_cards_enhanced()
    
    print(f"Successfully parsed {len(result['cards'])} cards and saved to guild_cards.json")
    
    # Save to file
    with open("guild_cards.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print faction ability
    if result.get("faction_ability"):
        print("Faction ability:")
        print(json.dumps(result["faction_ability"], indent=2))
    
    # Print sample card
    if result.get("cards"):
        print("Sample card data:")
        print(json.dumps(result["cards"][0], indent=2))
