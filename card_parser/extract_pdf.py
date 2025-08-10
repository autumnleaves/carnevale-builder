import PyPDF2
import json

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
        print(f"Error extracting text: {e}")
        return []

if __name__ == "__main__":
    pdf_path = "The_Guild_250801.pdf"
    pages = extract_text_from_pdf(pdf_path)
    
    print(f"Found {len(pages)} pages in PDF")
    
    # Save extracted text to JSON file
    output_file = "extracted_text.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pages, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted text saved to {output_file}")
    
    # Optional: Print all pages including the first one
    for page in pages:
        print(f"\n--- Page {page['page']} ---")
        print(page['text'])
        print("=" * 50)
