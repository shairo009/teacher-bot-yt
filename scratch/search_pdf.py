import PyPDF2

pdf_path = "C:/Users/1001s/Downloads/Lucent-General-Knowledge-GK-English-Medium.pdf"

def main():
    print("Opening Lucent GK PDF...")
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        num_pages = len(reader.pages)
        print(f"Total pages: {num_pages}")
        
        # Let's search for "Indian Polity" or "Constituent Assembly"
        found_pages = []
        for i in range(num_pages):
            # Scan only some pages first to be fast, e.g., first 300 pages
            if i % 10 == 0:
                print(f"Scanning page {i}...")
            page = reader.pages[i]
            text = page.extract_text()
            if "CONSTITUENT ASSEMBLY" in text.upper() or "INDIAN POLITY" in text.upper():
                print(f"Found on page {i + 1}")
                found_pages.append(i + 1)
                if len(found_pages) >= 15:
                    break
        print("Done searching. Found pages:", found_pages)

if __name__ == "__main__":
    main()
