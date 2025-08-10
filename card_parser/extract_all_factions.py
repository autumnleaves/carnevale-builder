import PyPDF2
import json
import os
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text_by_page = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                text_by_page.append({
                    'page': page_num + 1,
                    'text': text.strip()
                })
                
        return text_by_page
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return []

def get_faction_pdfs():
    """Find all faction PDF files in the current directory"""
    faction_pdfs = []
    
    # List of known faction PDF patterns
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    # Filter out rulebook PDFs
    faction_files = [f for f in pdf_files if 'Rulebook' not in f]
    
    return faction_files

def extract_faction_name(pdf_filename):
    """Extract faction name from PDF filename"""
    # Remove .pdf extension and date suffix
    name = pdf_filename.replace('.pdf', '')
    # Remove date patterns like _250801, _250214, etc.
    name = name.split('_')[0]
    # Handle special cases
    if name == 'The':
        # For files like "The_Guild_250801.pdf", "The_Doctors_250321.pdf"
        parts = pdf_filename.replace('.pdf', '').split('_')
        if len(parts) >= 2:
            name = '_'.join(parts[:-1])  # Everything except the date
    return name

if __name__ == "__main__":
    faction_pdfs = get_faction_pdfs()
    
    print(f"Found {len(faction_pdfs)} faction PDFs:")
    for pdf in faction_pdfs:
        print(f"  - {pdf}")
    
    results = {}
    
    for pdf_file in faction_pdfs:
        print(f"\nProcessing {pdf_file}...")
        
        # Extract text from PDF
        pages = extract_text_from_pdf(pdf_file)
        
        if pages:
            print(f"  Extracted {len(pages)} pages")
            
            # Get faction name for output files
            faction_name = extract_faction_name(pdf_file)
            
            # Save extracted text to JSON file
            text_output_file = f"{faction_name}_extracted_text.json"
            with open(text_output_file, 'w', encoding='utf-8') as f:
                json.dump(pages, f, indent=2, ensure_ascii=False)
            
            print(f"  Saved extracted text to {text_output_file}")
            
            results[faction_name] = {
                'pdf_file': pdf_file,
                'pages': len(pages),
                'text_file': text_output_file
            }
        else:
            print(f"  Failed to extract text from {pdf_file}")
    
    # Save summary of all processed files
    with open('extraction_summary.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessing complete. Summary saved to extraction_summary.json")
    print(f"Successfully processed {len(results)} faction PDFs")
