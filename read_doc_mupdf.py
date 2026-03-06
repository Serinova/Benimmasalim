import fitz
pdf_path = r"c:/Users/yusuf/OneDrive/Belgeler/BenimMasalim/book_1158cdb3-9927-4ff7-8720-c130719b1f76.pdf"
doc = fitz.open(pdf_path)
for page_num in range(len(doc)):
    page = doc.load_page(page_num)
    text = page.get_text()
    if text.strip():
        print(f"--- PAGE {page_num+1} TEXT ---")
        print(text.strip())
    else:
        images = page.get_images(full=True)
        print(f"--- PAGE {page_num+1} NO TEXT. Found {len(images)} images ---")
