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
    """Find all faction PDF files in the pdfs directory"""
    faction_pdfs = []
    
    # Check if pdfs directory exists
    pdfs_dir = Path('pdfs')
    if not pdfs_dir.exists():
        print("Warning: 'pdfs' directory not found. Looking in current directory instead.")
        pdfs_dir = Path('.')
    
    # List of known faction PDF patterns
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]
    
    # Filter out rulebook PDFs
    faction_files = [f for f in pdf_files if 'Rulebook' not in f]
    
    # Return full paths to the PDFs
    return [str(pdfs_dir / f) for f in faction_files]

def extract_faction_name(pdf_filepath):
    """Extract faction name from PDF filepath"""
    # Get just the filename from the full path
    pdf_filename = Path(pdf_filepath).name
    
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
    # Ensure extracted_text directory exists
    extracted_text_dir = Path('extracted_text')
    extracted_text_dir.mkdir(exist_ok=True)
    
    faction_pdfs = get_faction_pdfs()
    
    print(f"Found {len(faction_pdfs)} faction PDFs:")
    for pdf in faction_pdfs:
        print(f"  - {pdf}")
    
    results = {}
    
    for pdf_path in faction_pdfs:
        pdf_filename = Path(pdf_path).name
        print(f"\nProcessing {pdf_filename}...")
        
        # Extract text from PDF
        pages = extract_text_from_pdf(pdf_path)
        
        if pages:
            print(f"  Extracted {len(pages)} pages")
            
            # Get faction name for output files
            faction_name = extract_faction_name(pdf_path)
            
            # Save extracted text to JSON file in extracted_text directory
            text_output_file = f"extracted_text/{faction_name}_extracted_text.json"
            with open(text_output_file, 'w', encoding='utf-8') as f:
                json.dump(pages, f, indent=2, ensure_ascii=False)
            
            print(f"  Saved extracted text to {text_output_file}")
            
            results[faction_name] = {
                'pdf_file': pdf_filename,
                'pages': len(pages),
                'text_file': text_output_file
            }
        else:
            print(f"  Failed to extract text from {pdf_filename}")
    
    # Save summary of all processed files
    with open('extraction_summary.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nProcessing complete. Summary saved to extraction_summary.json")
    print(f"Successfully processed {len(results)} faction PDFs")
