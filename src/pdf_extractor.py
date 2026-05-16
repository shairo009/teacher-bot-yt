import os
import json
from pathlib import Path
import re

class PDFExtractor:
    """Extract and chunk text from actual PDF files."""

    def __init__(self, books_dir="data/books"):
        self.books_dir = Path(books_dir)
        self.all_content = []

    def extract_all(self, book_list=None):
        """Scan data/books for PDFs and extract text."""
        try:
            import pdfplumber
        except ImportError:
            print("pdfplumber not installed. Please pip install pdfplumber")
            return []

        all_content = []
        
        if not self.books_dir.exists():
            print(f"Books directory {self.books_dir} not found.")
            return []
            
        for class_dir in self.books_dir.iterdir():
            if not class_dir.is_dir(): continue
            
            # Extract class number from dir name, e.g. class_1_math -> 1
            class_match = re.search(r'class_(\d+)', class_dir.name)
            class_num = int(class_match.group(1)) if class_match else 1
            
            chapters = []
            
            # Iterate through PDFs in this class directory
            pdf_files = sorted(list(class_dir.glob("*.pdf")))
            for pdf_path in pdf_files:
                print(f"  Extracting {pdf_path.name}...")
                text_content = ""
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                text_content += text + "\n"
                except Exception as e:
                    print(f"    Failed to read PDF: {e}")
                    continue
                
                # Chunk text into paragraphs
                paragraphs = [p.strip() for p in text_content.split('\n\n') if len(p.strip()) > 30]
                
                if not paragraphs:
                    continue
                    
                # Use filename as chapter name
                chapter_name = pdf_path.stem
                
                chapters.append({
                    'chapter': chapter_name,
                    'topics': paragraphs  # Each paragraph is a "topic"
                })
            
            if chapters:
                all_content.append({
                    'class': class_num,
                    'medium': 'English',
                    'chapters': chapters,
                    'source': 'pdf'
                })
                
        return all_content

    def build_topic_index(self, all_content):
        """Build flat index of all chunks in order."""
        index = []
        topic_id = 0

        for book in sorted(all_content, key=lambda x: x.get('class', 1)):
            class_num = book['class']
            medium = book['medium']
            chapters = book['chapters']

            for chapter in chapters:
                chapter_name = chapter['chapter']
                topics = chapter['topics']

                for topic_idx, topic_text in enumerate(topics):
                    topic_id += 1
                    index.append({
                        'id': topic_id,
                        'class': class_num,
                        'medium': medium,
                        'chapter': chapter_name,
                        'topic_idx': topic_idx,
                        'topic': topic_text,  # This is now the raw textbook paragraph!
                        'source': 'pdf'
                    })

        return index

    def save_index(self, index, path="data/topics_index.json"):
        """Save topic index to JSON file."""
        os.makedirs(os.path.dirname(path) or 'data', exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_topics': len(index),
                'topics': index
            }, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(index)} PDF topics to {path}")
        return index

if __name__ == "__main__":
    extractor = PDFExtractor()
    all_content = extractor.extract_all()
    index = extractor.build_topic_index(all_content)
    extractor.save_index(index)
    print(f"Total PDF chunks extracted: {len(index)}")