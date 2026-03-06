import sys
# imported pypdf2
# PyPDF2 was replaced by pypdf, pypdf2 might still work but pypdf is modern. we installed pypdf2.

try:
    from PyPDF2 import PdfReader
    pdf_path = r"c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/book_1158cdb3-9927-4ff7-8720-c130719b1f76.pdf"
    reader = PdfReader(pdf_path)
    
    print(f"Number of pages: {len(reader.pages)}")
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        print(f"--- PAGE {i+1} ---")
        print(text if text else "[NO TEXT]")
        print("-------------------")
except Exception as e:
    print(e)
