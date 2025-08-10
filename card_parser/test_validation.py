#!/usr/bin/env python3
"""
Test suite for validating parsed card JSON files against their extracted text counterparts.
"""

import json
import os
import sys
from typing import Dict, List, Set, Any, Tuple


class CardValidationTests:
    def __init__(self, json_file: str, extracted_text_file: str, parsed_abilities_file: str = "parsed_abilities.json"):
        """Initialize the test suite with file paths."""
        self.json_file = json_file
        self.extracted_text_file = extracted_text_file
        self.parsed_abilities_file = parsed_abilities_file
        
        # Load the data
        self.json_data = self._load_json(json_file)
        self.extracted_data = self._load_json(extracted_text_file)
        self.parsed_abilities = self._load_json(parsed_abilities_file)
        
        self.errors = []
        self.warnings = []
    
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            sys.exit(1)
    
    def _add_error(self, test_name: str, message: str):
        """Add an error to the error list."""
        self.errors.append(f"{test_name}: {message}")
    
    def _add_warning(self, test_name: str, message: str):
        """Add a warning to the warning list."""
        self.warnings.append(f"{test_name}: {message}")
    
    def test_page_mapping(self) -> bool:
        """Test 1: Validate 1:1 mapping between extracted text pages and parsed cards."""
        test_name = "Page Mapping"
        
        # Get all pages from extracted text (excluding page 1 which is faction ability)
        extracted_pages = set()
        if isinstance(self.extracted_data, list):
            # Handle list format
            for entry in self.extracted_data:
                if isinstance(entry, dict) and "page" in entry:
                    page_int = int(entry["page"])
                    if page_int > 1:  # Skip page 1 (faction ability)
                        extracted_pages.add(page_int)
        else:
            # Handle dict format with pages key
            for page_num, content in self.extracted_data.get("pages", {}).items():
                page_int = int(page_num)
                if page_int > 1:  # Skip page 1 (faction ability)
                    extracted_pages.add(page_int)
        
        # Get all pages from parsed cards
        parsed_pages = set()
        for card in self.json_data.get("cards", []):
            if "page" in card and card["page"] is not None:
                parsed_pages.add(card["page"])
        
        # Check for missing pages in parsed data
        missing_in_parsed = extracted_pages - parsed_pages
        if missing_in_parsed:
            self._add_error(test_name, f"Pages in extracted text but not in parsed cards: {sorted(missing_in_parsed)}")
        
        # Check for extra pages in parsed data
        extra_in_parsed = parsed_pages - extracted_pages
        if extra_in_parsed:
            self._add_error(test_name, f"Pages in parsed cards but not in extracted text: {sorted(extra_in_parsed)}")
        
        return len(self.errors) == 0
    
    def test_required_fields(self) -> bool:
        """Test 2: Validate required fields are non-null and non-empty."""
        test_name = "Required Fields"
        required_fields = ["name", "rank", "version", "actions", "life", "base_size", "ducats"]
        
        for i, card in enumerate(self.json_data.get("cards", [])):
            card_name = card.get("name", f"Card #{i+1}")
            
            # Check required fields
            for field in required_fields:
                if field not in card or card[field] is None:
                    self._add_error(test_name, f"{card_name}: Missing or null field '{field}'")
                elif isinstance(card[field], str) and card[field].strip() == "":
                    self._add_error(test_name, f"{card_name}: Empty field '{field}'")
            
            # Check stat_block
            if "stat_block" not in card or not card["stat_block"]:
                self._add_error(test_name, f"{card_name}: Missing or empty stat_block")
            else:
                stat_fields = ["movement", "dexterity", "attack", "protection", "mind"]
                for stat_field in stat_fields:
                    if stat_field not in card["stat_block"] or card["stat_block"][stat_field] is None:
                        self._add_error(test_name, f"{card_name}: Missing or null stat_block.{stat_field}")
        
        return len(self.errors) == 0
    
    def test_no_duplicate_common_abilities(self) -> bool:
        """Test 3: Validate no duplicate common abilities in the same card."""
        test_name = "No Duplicate Common Abilities"
        
        for card in self.json_data.get("cards", []):
            card_name = card.get("name", "Unknown Card")
            common_abilities = card.get("abilities", {}).get("common", [])
            
            # Check for duplicates
            seen_abilities = set()
            duplicates = set()
            
            for ability in common_abilities:
                if ability in seen_abilities:
                    duplicates.add(ability)
                seen_abilities.add(ability)
            
            if duplicates:
                self._add_error(test_name, f"{card_name}: Duplicate common abilities: {sorted(duplicates)}")
        
        return len(self.errors) == 0
    
    def test_common_abilities_in_reference(self) -> bool:
        """Test 4: Validate all common abilities appear in parsed_abilities.json."""
        test_name = "Common Abilities Reference Check"
        
        # Build a set of reference abilities with (X) pattern matching
        reference_abilities = set()
        for ability in self.parsed_abilities.get("common_abilities", []):
            reference_abilities.add(ability)
        
        def matches_reference(card_ability: str) -> bool:
            """Check if a card ability matches any reference ability, handling (X) wildcards."""
            # Direct match first
            if card_ability in reference_abilities:
                return True
            
            # Check for (X) pattern matches
            for ref_ability in reference_abilities:
                if "(X)" in ref_ability:
                    # Create pattern from reference ability
                    pattern_parts = ref_ability.split("(X)")
                    if len(pattern_parts) == 2:
                        prefix, suffix = pattern_parts
                        # Check if card ability starts with prefix and ends with suffix
                        if (card_ability.startswith(prefix) and 
                            card_ability.endswith(suffix) and 
                            len(card_ability) > len(prefix) + len(suffix)):
                            # Extract the middle part and check if it's in parentheses
                            middle = card_ability[len(prefix):-len(suffix) if suffix else len(card_ability)]
                            if middle.startswith("(") and middle.endswith(")"):
                                return True
            
            return False
        
        for card in self.json_data.get("cards", []):
            card_name = card.get("name", "Unknown Card")
            common_abilities = card.get("abilities", {}).get("common", [])
            
            for ability in common_abilities:
                if not matches_reference(ability):
                    self._add_error(test_name, f"{card_name}: Common ability '{ability}' not found in reference")
        
        return len(self.errors) == 0
    
    def test_unique_ability_names(self) -> bool:
        """Test 5: Validate unique and command abilities have unique names within each card."""
        test_name = "Unique Ability Names"
        
        for card in self.json_data.get("cards", []):
            card_name = card.get("name", "Unknown Card")
            abilities = card.get("abilities", {})
            
            # Collect all ability names from unique and command sections
            all_ability_names = []
            
            # Unique abilities
            unique_abilities = abilities.get("unique", [])
            for ability in unique_abilities:
                if isinstance(ability, dict) and "name" in ability:
                    all_ability_names.append(("unique", ability["name"]))
            
            # Command abilities
            command_abilities = abilities.get("command", [])
            for ability in command_abilities:
                if isinstance(ability, dict) and "name" in ability:
                    all_ability_names.append(("command", ability["name"]))
            
            # Check for duplicates
            seen_names = set()
            for ability_type, ability_name in all_ability_names:
                if ability_name in seen_names:
                    self._add_error(test_name, f"{card_name}: Duplicate ability name '{ability_name}' appears in multiple sections")
                seen_names.add(ability_name)
        
        return len(self.errors) == 0
    
    def test_ability_completeness(self) -> bool:
        """Test 6: Validate all unique and command abilities have non-empty names and descriptions."""
        test_name = "Ability Completeness"
        
        for card in self.json_data.get("cards", []):
            card_name = card.get("name", "Unknown Card")
            abilities = card.get("abilities", {})
            
            # Check unique abilities
            unique_abilities = abilities.get("unique", [])
            for i, ability in enumerate(unique_abilities):
                if not isinstance(ability, dict):
                    self._add_error(test_name, f"{card_name}: Unique ability #{i+1} is not a dictionary")
                    continue
                
                # Check name
                if "name" not in ability or not ability["name"] or ability["name"].strip() == "":
                    self._add_error(test_name, f"{card_name}: Unique ability #{i+1} missing or empty name")
                
                # Check description
                if "description" not in ability or not ability["description"] or ability["description"].strip() == "":
                    self._add_error(test_name, f"{card_name}: Unique ability '{ability.get('name', f'#{i+1}')}' missing or empty description")
            
            # Check command abilities
            command_abilities = abilities.get("command", [])
            for i, ability in enumerate(command_abilities):
                if not isinstance(ability, dict):
                    self._add_error(test_name, f"{card_name}: Command ability #{i+1} is not a dictionary")
                    continue
                
                # Check name
                if "name" not in ability or not ability["name"] or ability["name"].strip() == "":
                    self._add_error(test_name, f"{card_name}: Command ability #{i+1} missing or empty name")
                
                # Check description
                if "description" not in ability or not ability["description"] or ability["description"].strip() == "":
                    self._add_error(test_name, f"{card_name}: Command ability '{ability.get('name', f'#{i+1}')}' missing or empty description")
        
        return len(self.errors) == 0
    
    def test_weapon_names(self) -> bool:
        """Test 7: Validate all weapons have names."""
        test_name = "Weapon Names"
        
        for card in self.json_data.get("cards", []):
            card_name = card.get("name", "Unknown Card")
            weapons = card.get("weapons", [])
            
            for i, weapon in enumerate(weapons):
                if not isinstance(weapon, dict):
                    self._add_error(test_name, f"{card_name}: Weapon #{i+1} is not a dictionary")
                    continue
                
                if "name" not in weapon or not weapon["name"] or weapon["name"].strip() == "":
                    self._add_error(test_name, f"{card_name}: Weapon #{i+1} missing or empty name")
        
        return len(self.errors) == 0
    
    def test_faction_ability(self) -> bool:
        """Test 8: Validate faction ability has non-empty name and description."""
        test_name = "Faction Ability"
        
        faction_ability = self.json_data.get("faction_ability", {})
        
        if not faction_ability:
            self._add_error(test_name, "Missing faction_ability")
            return False
        
        # Check name
        if "name" not in faction_ability or not faction_ability["name"] or faction_ability["name"].strip() == "":
            self._add_error(test_name, "Faction ability missing or empty name")
        
        # Check description
        if "description" not in faction_ability or not faction_ability["description"] or faction_ability["description"].strip() == "":
            self._add_error(test_name, "Faction ability missing or empty description")
        
        return len(self.errors) == 0
    
    def run_all_tests(self) -> Tuple[int, int]:
        """Run all tests and return (passed, total) counts."""
        tests = [
            self.test_page_mapping,
            self.test_required_fields,
            self.test_no_duplicate_common_abilities,
            self.test_common_abilities_in_reference,
            self.test_unique_ability_names,
            self.test_ability_completeness,
            self.test_weapon_names,
            self.test_faction_ability,
        ]
        
        passed = 0
        total = len(tests)
        
        print(f"Running validation tests for {self.json_file}")
        print("=" * 60)
        
        for test in tests:
            test_name = test.__name__.replace("test_", "").replace("_", " ").title()
            error_count_before = len(self.errors)
            
            try:
                test()
                if len(self.errors) == error_count_before:
                    print(f"✓ {test_name}")
                    passed += 1
                else:
                    print(f"✗ {test_name}")
            except Exception as e:
                print(f"✗ {test_name} (Exception: {e})")
                self._add_error(test_name, f"Test failed with exception: {e}")
        
        return passed, total
    
    def print_results(self):
        """Print detailed results of all tests."""
        print("\n" + "=" * 60)
        
        if self.errors:
            print("ERRORS FOUND:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if not self.errors and not self.warnings:
            print("✓ All tests passed with no errors or warnings!")


def main():
    """Main function to run tests on specified files."""
    if len(sys.argv) < 3:
        print("Usage: python test_validation.py <json_file> <extracted_text_file> [parsed_abilities_file]")
        print("Example: python test_validation.py the_guild_cards.json the_guild_extracted_text.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    extracted_text_file = sys.argv[2]
    parsed_abilities_file = sys.argv[3] if len(sys.argv) > 3 else "parsed_abilities.json"
    
    # Check if files exist
    for file_path in [json_file, extracted_text_file, parsed_abilities_file]:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
    
    # Run tests
    validator = CardValidationTests(json_file, extracted_text_file, parsed_abilities_file)
    passed, total = validator.run_all_tests()
    validator.print_results()
    
    print(f"\n{passed}/{total} tests passed")
    
    # Exit with error code if any tests failed
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
