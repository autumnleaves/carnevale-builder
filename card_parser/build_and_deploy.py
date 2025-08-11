#!/usr/bin/env python3
"""
Build and Deploy Script for Carnevale Card Parser

This script orchestrates the complete pipeline:
1. Parse all faction cards using parse_cards.py
2. Run validation tests using test_all_factions.py
3. If validation passes, deploy cards to webapp

Usage: python build_and_deploy.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import importlib.util

def run_script_directly(script_name, description):
    """Run a Python script directly by importing and executing it."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    
    # Save current stdout to restore later
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    try:
        # Import and run the script
        spec = importlib.util.spec_from_file_location("script_module", script_name)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load script: {script_name}")
            
        script_module = importlib.util.module_from_spec(spec)
        
        # Temporarily redirect stdout to capture any print statements
        from io import StringIO
        captured_output = StringIO()
        sys.stdout = captured_output
        sys.stderr = captured_output
        
        # Execute the script
        spec.loader.exec_module(script_module)
        
        # Restore stdout and get captured output
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        output = captured_output.getvalue()
        
        print(output)
        return True
        
    except Exception as e:
        # Restore stdout/stderr in case of error
        sys.stdout = original_stdout 
        sys.stderr = original_stderr
        print(f"❌ ERROR: {e}")
        return False

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"{'='*60}")
    
    try:
        # Set environment to handle Unicode properly in Windows
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True, encoding='utf-8',
                              env=env)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Command failed with return code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def ensure_directories():
    """Ensure required directories exist."""
    print("Checking directory structure...")
    
    required_dirs = [
        "pdfs",
        "extracted_text", 
        "output",
        "../webapp"
    ]
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ Missing required directory: {dir_path}")
            return False
        print(f"✓ Found: {dir_path}")
    
    # Create webapp/cards directory if it doesn't exist
    webapp_cards_dir = Path("../webapp/cards")
    webapp_cards_dir.mkdir(exist_ok=True)
    print(f"✓ Created/verified: {webapp_cards_dir}")
    
    return True

def check_required_files():
    """Check that required files exist."""
    print("\nChecking required files...")
    
    required_files = [
        "parse_cards.py",
        "test_all_factions.py", 
        "parsed_abilities.json"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing required file: {file_path}")
            return False
        print(f"✓ Found: {file_path}")
    
    # Check for extracted text files
    extracted_files = list(Path("extracted_text").glob("*_extracted_text.json"))
    if not extracted_files:
        print("❌ No extracted text files found in extracted_text/")
        return False
    print(f"✓ Found {len(extracted_files)} extracted text files")
    
    return True

def parse_cards():
    """Run the card parsing script."""
    return run_script_directly("parse_cards.py", "Parsing faction cards")

def validate_cards():
    """Run the validation tests."""
    return run_script_directly("test_all_factions.py", "Validating parsed cards")

def deploy_to_webapp():
    """Copy parsed cards to webapp directory."""
    print(f"\n{'='*60}")
    print("STEP: Deploying cards to webapp")
    print(f"{'='*60}")
    
    try:
        output_dir = Path("output")
        webapp_cards_dir = Path("../webapp/cards")
        
        # Get list of card files
        card_files = list(output_dir.glob("*_cards.json"))
        
        if not card_files:
            print("❌ No card files found in output directory")
            return False
        
        print(f"Deploying {len(card_files)} card files...")
        
        for card_file in card_files:
            dest_file = webapp_cards_dir / card_file.name
            shutil.copy2(card_file, dest_file)
            print(f"✓ Copied: {card_file.name}")
        
        # Create an index file with metadata
        create_cards_index(card_files, webapp_cards_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        return False

def create_cards_index(card_files, webapp_cards_dir):
    """Create an index file with metadata about all available card sets."""
    print("Creating cards index...")
    
    index_data = {
        "factions": [],
        "generated_at": "2025-08-10",  # Current date
        "total_factions": len(card_files)
    }
    
    for card_file in sorted(card_files):
        try:
            with open(card_file, 'r', encoding='utf-8') as f:
                card_data = json.load(f)
            
            faction_info = {
                "file": card_file.name,
                "faction": card_data.get("faction", "Unknown"),
                "cards_count": len(card_data.get("cards", [])),
                "faction_ability": card_data.get("faction_ability", "Unknown")
            }
            index_data["factions"].append(faction_info)
            
        except Exception as e:
            print(f"⚠️  Warning: Could not read metadata from {card_file.name}: {e}")
            # Add basic info even if we can't read the file
            faction_info = {
                "file": card_file.name,
                "faction": card_file.stem.replace("_cards", "").replace("_", " ").title(),
                "cards_count": "Unknown",
                "faction_ability": "Unknown"
            }
            index_data["factions"].append(faction_info)
    
    # Save index
    index_file = webapp_cards_dir / "index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created: {index_file}")
    print(f"  - {len(index_data['factions'])} factions indexed")

def print_summary(success):
    """Print final summary."""
    print(f"\n{'='*60}")
    print("BUILD AND DEPLOY SUMMARY")
    print(f"{'='*60}")
    
    if success:
        print("🎉 SUCCESS: All steps completed successfully!")
        print("\nWhat was accomplished:")
        print("✓ Cards parsed from extracted text")
        print("✓ All validation tests passed")
        print("✓ Cards deployed to webapp/cards/")
        print("✓ Webapp compatibility maintained")
        print("✓ Cards index created")
        
        print("\n📁 Webapp now contains:")
        webapp_cards_dir = Path("../webapp/cards")
        if webapp_cards_dir.exists():
            card_files = list(webapp_cards_dir.glob("*.json"))
            for card_file in sorted(card_files):
                print(f"   - {card_file.name}")
        
        print(f"\n🚀 Ready to serve! Run 'python -m http.server 8000' in the webapp directory.")
        
    else:
        print("❌ FAILED: Pipeline did not complete successfully")
        print("\nTroubleshooting:")
        print("- Check that all required directories exist (pdfs/, extracted_text/)")
        print("- Ensure parsed_abilities.json exists")
        print("- Verify extraction was run successfully")
        print("- Check console output above for specific errors")

def main():
    """Main orchestration function."""
    print("🎯 CARNEVALE CARD PARSER - BUILD AND DEPLOY")
    print("=" * 60)
    
    # Step 1: Check environment
    if not ensure_directories():
        print_summary(False)
        sys.exit(1)
    
    if not check_required_files():
        print_summary(False)
        sys.exit(1)
    
    # Step 2: Parse cards
    if not parse_cards():
        print("❌ Card parsing failed. Stopping.")
        print_summary(False)
        sys.exit(1)
    
    # Step 3: Validate cards
    if not validate_cards():
        print("❌ Card validation failed. Stopping.")
        print_summary(False)
        sys.exit(1)
    
    # Step 4: Deploy to webapp
    if not deploy_to_webapp():
        print("❌ Deployment to webapp failed. Stopping.")
        print_summary(False)
        sys.exit(1)
    
    # Success!
    print_summary(True)

if __name__ == "__main__":
    main()
