import PyPDF2
import json

def extract_rulebook_pages(pdf_path, start_page, end_page):
    """Extract specific pages from the rulebook PDF"""
    pages = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract pages (convert to 0-indexed)
            for page_num in range(start_page - 1, min(end_page, len(pdf_reader.pages))):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                pages.append({
                    'page': page_num + 1,
                    'text': text.strip()
                })
                
        return pages
    except Exception as e:
        print(f"Error extracting text: {e}")
        return []

def parse_common_abilities(pages):
    """Parse common ability names from pages 36-38"""
    common_abilities = []
    
    for page_data in pages:
        if page_data['page'] in [36, 37, 38]:  # Common abilities pages
            text = page_data['text']
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip headers, footers, and page numbers
                if (not line or 
                    line.isdigit() or 
                    'Campaigns Actions Special Rules The Basics' in line or
                    line.lower().startswith('special rules') or
                    line.lower().startswith('character abilities') or
                    line.lower().startswith('weapon abilities') or
                    len(line) > 100):  # Skip long paragraphs
                    continue
                
                # Look for ability names - they typically:
                # 1. Start with capital letter
                # 2. Are short (usually < 30 chars)
                # 3. May have (X) notation
                # 4. Are followed by description text on next lines
                if (line and 
                    len(line) <= 30 and
                    line[0].isupper() and
                    not line.endswith('.') and  # Descriptions end with periods
                    not line.startswith('This character') and  # Skip descriptions
                    not line.startswith('If ') and
                    not line.startswith('For ') and
                    not line.startswith('While ') and
                    not line.startswith('When ') and
                    not line.startswith('At ') and
                    not line.startswith('Additionally')):
                    
                    # Check if next line looks like a description (starts with "This character" etc.)
                    next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    if (next_line and 
                        (next_line.startswith('This character') or 
                         next_line.startswith('If ') or
                         next_line.startswith('While ') or
                         next_line.startswith('When ') or
                         next_line.startswith('For ') or
                         next_line.startswith('At '))):
                        common_abilities.append(line)
    
    return sorted(list(set(common_abilities)))  # Remove duplicates and sort

def parse_weapon_abilities(pages):
    """Parse weapon ability names from pages 39-40"""
    weapon_abilities = []
    
    for page_data in pages:
        if page_data['page'] in [39, 40]:  # Weapon abilities pages
            text = page_data['text']
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip headers, footers, and page numbers
                if (not line or 
                    line.isdigit() or 
                    'Campaigns Actions Special Rules The Basics' in line or
                    line.lower().startswith('weapon abilities') or
                    len(line) > 100):  # Skip long paragraphs
                    continue
                
                # Look for weapon ability names - similar pattern to character abilities
                if (line and 
                    len(line) <= 30 and
                    line[0].isupper() and
                    not line.endswith('.') and  # Descriptions end with periods
                    not line.startswith('This weapon') and  # Skip descriptions
                    not line.startswith('A character') and
                    not line.startswith('If ') and
                    not line.startswith('For ') and
                    not line.startswith('While ') and
                    not line.startswith('When ') and
                    not line.startswith('Any ') and
                    not line.startswith('The ')):
                    
                    # Check if next line looks like a description
                    next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    if (next_line and 
                        (next_line.startswith('This weapon') or 
                         next_line.startswith('A character') or
                         next_line.startswith('If ') or
                         next_line.startswith('While ') or
                         next_line.startswith('When ') or
                         next_line.startswith('For ') or
                         next_line.startswith('Any ') or
                         next_line.startswith('The '))):
                        weapon_abilities.append(line)
    
    return sorted(list(set(weapon_abilities)))  # Remove duplicates and sort

if __name__ == "__main__":
    # Extract pages 36-40 from the rulebook
    rulebook_path = "Desktop_Carnevale_Rulebook_2.3.pdf"
    pages = extract_rulebook_pages(rulebook_path, 36, 40)
    
    if not pages:
        print("No pages extracted. Check if the PDF file exists.")
        exit(1)
    
    print(f"Extracted {len(pages)} pages from rulebook")
    
    # Save raw extracted text to file
    raw_output_file = "rulebook_pages_36_40_raw.txt"
    with open(raw_output_file, 'w', encoding='utf-8') as f:
        for page_data in pages:
            f.write(f"=== PAGE {page_data['page']} ===\n")
            f.write(page_data['text'])
            f.write(f"\n{'='*50}\n\n")
    
    print(f"Raw text saved to {raw_output_file}")
    
    # Parse abilities
    common_abilities = parse_common_abilities(pages)
    weapon_abilities = parse_weapon_abilities(pages)
    
    # Save parsed abilities to JSON
    abilities_data = {
        "common_abilities": sorted(common_abilities),
        "weapon_abilities": sorted(weapon_abilities),
        "source_pages": [36, 37, 38, 39, 40],
        "extraction_notes": {
            "common_abilities_pages": [36, 37, 38],
            "weapon_abilities_pages": [39, 40],
            "total_common_found": len(common_abilities),
            "total_weapon_found": len(weapon_abilities)
        }
    }
    
    abilities_output_file = "parsed_abilities.json"
    with open(abilities_output_file, 'w', encoding='utf-8') as f:
        json.dump(abilities_data, f, indent=2, ensure_ascii=False)
    
    print(f"Parsed abilities saved to {abilities_output_file}")
    print(f"Found {len(common_abilities)} common abilities")
    print(f"Found {len(weapon_abilities)} weapon abilities")
    
    # Display sample findings
    if common_abilities:
        print(f"\nSample common abilities:")
        for ability in sorted(common_abilities)[:10]:
            print(f"  - {ability}")
    
    if weapon_abilities:
        print(f"\nSample weapon abilities:")
        for ability in sorted(weapon_abilities)[:10]:
            print(f"  - {ability}")
