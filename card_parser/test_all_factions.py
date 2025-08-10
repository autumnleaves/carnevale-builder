#!/usr/bin/env python3
"""
Batch test runner for validating all parsed faction JSON files.
"""

import os
import sys
import glob
from test_validation import CardValidationTests


def find_faction_files():
    """Find all faction JSON files and their corresponding extracted text files."""
    # Find all *_cards.json files in the output directory
    json_files = glob.glob("output/*_cards.json")
    
    faction_pairs = []
    for json_file in json_files:
        # Extract faction name (remove path and _cards.json suffix)
        faction_name = os.path.basename(json_file).replace("_cards.json", "")
        
        # Look for corresponding extracted text file in extracted_text directory
        extracted_text_file = f"extracted_text/{faction_name}_extracted_text.json"
        
        if os.path.exists(extracted_text_file):
            faction_pairs.append((json_file, extracted_text_file, faction_name))
        else:
            print(f"Warning: No extracted text file found for {json_file}")
    
    return faction_pairs


def main():
    """Run validation tests on all faction files."""
    parsed_abilities_file = "parsed_abilities.json"
    
    # Check if parsed_abilities.json exists
    if not os.path.exists(parsed_abilities_file):
        print(f"Error: {parsed_abilities_file} not found. This file is required for validation.")
        sys.exit(1)
    
    # Find all faction files
    faction_pairs = find_faction_files()
    
    if not faction_pairs:
        print("No faction files found to test.")
        sys.exit(1)
    
    print(f"Found {len(faction_pairs)} faction(s) to test:")
    for json_file, extracted_file, faction_name in faction_pairs:
        print(f"  • {faction_name}: {json_file} + {extracted_file}")
    
    print("\n" + "=" * 80)
    
    # Run tests for each faction
    total_passed = 0
    total_tests = 0
    failed_factions = []
    
    for json_file, extracted_file, faction_name in faction_pairs:
        print(f"\nTesting {faction_name.upper()}")
        print("-" * 40)
        
        try:
            validator = CardValidationTests(json_file, extracted_file, parsed_abilities_file)
            passed, total = validator.run_all_tests()
            
            total_passed += passed
            total_tests += total
            
            if passed < total:
                failed_factions.append(faction_name)
                print(f"\n{faction_name}: {passed}/{total} tests passed ❌")
                validator.print_results()
            else:
                print(f"\n{faction_name}: {passed}/{total} tests passed ✅")
        
        except Exception as e:
            print(f"Error testing {faction_name}: {e}")
            failed_factions.append(faction_name)
            total_tests += 8  # Assume 8 tests per faction
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    print(f"Total tests run: {total_tests}")
    print(f"Total tests passed: {total_passed}")
    print(f"Success rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "0%")
    
    if failed_factions:
        print(f"\nFactions with failures: {', '.join(failed_factions)}")
        print("❌ Some tests failed")
        sys.exit(1)
    else:
        print("\n✅ All factions passed all tests!")


if __name__ == "__main__":
    main()
