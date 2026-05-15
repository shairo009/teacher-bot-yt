import os
import json
import re
from pathlib import Path

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


class PDFExtractor:
    def __init__(self, books_dir="data/books"):
        self.books_dir = Path(books_dir)
        self.topics = []
        self.class_map = {}

    def extract_from_pypdf2(self, pdf_path):
        """Extract text using PyPDF2."""
        topics = []
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""

                # Parse chapters from text
                chapters = self._parse_chapters(text)
                topics.extend(chapters)
        except Exception as e:
            print(f"  PyPDF2 extraction failed: {e}")
        return topics

    def extract_from_pdfplumber(self, pdf_path):
        """Extract text using pdfplumber (better extraction)."""
        topics = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"

                chapters = self._parse_chapters(text)
                topics.extend(chapters)
        except Exception as e:
            print(f"  pdfplumber extraction failed: {e}")
        return topics

    def _parse_chapters(self, text):
        """Parse chapters and topics from extracted text."""
        chapters = []

        # Common patterns for chapter headings
        # Pattern 1: Chapter X. Title
        # Pattern 2: CHAPTER X or CHAPTER - X
        chapter_patterns = [
            r'Chapter\s+(\d+)[:\.\s]+([A-Za-z0-9\s]+?)(?=\n|$)',
            r'CHAPTER\s+(\d+)[:\.\s]+([A-Za-z0-9\s]+?)(?=\n|$)',
            r'(\d+)\.\s+([A-Za-z][A-Za-z\s]+?)(?=\n)',
        ]

        lines = text.split('\n')
        current_chapter = None
        current_topic = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            matched = False
            for pattern in chapter_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous chapter
                    if current_chapter and current_topic:
                        chapters.append({
                            'chapter': current_chapter,
                            'topics': current_topic
                        })

                    # Start new chapter
                    ch_num = match.group(1)
                    ch_title = match.group(2).strip() if len(match.groups()) > 1 else ""
                    current_chapter = f"Chapter {ch_num}"
                    if ch_title:
                        current_chapter += f": {ch_title}"
                    current_topic = []
                    matched = True
                    break

            if not matched and current_chapter and len(line) > 5:
                # This is content under current chapter
                # Clean and add as a sub-topic
                clean_line = re.sub(r'\s+', ' ', line)
                clean_line = re.sub(r'^\d+[\.\)]\s*', '', clean_line)
                if len(clean_line) > 10 and len(clean_line) < 200:
                    current_topic.append(clean_line[:500])

        # Don't forget last chapter
        if current_chapter and current_topic:
            chapters.append({
                'chapter': current_chapter,
                'topics': current_topic
            })

        return chapters

    def extract_all(self, pdf_paths):
        """Extract topics from all PDF files."""
        all_content = []

        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                print(f"  PDF not found: {pdf_path}")
                continue

            filename = Path(pdf_path).stem
            # Extract class from filename (e.g., "class6_english")
            class_match = re.search(r'class(\d+)', filename, re.IGNORECASE)
            medium_match = re.search(r'(english|hindi)', filename, re.IGNORECASE)

            class_num = int(class_match.group(1)) if class_match else 0
            medium = medium_match.group(1) if medium_match else "English"

            print(f"  Extracting: {filename} (Class {class_num}, {medium})")

            topics = []
            if HAS_PDFPLUMBER:
                topics = self.extract_from_pdfplumber(pdf_path)
            elif HAS_PYPDF2:
                topics = self.extract_from_pypdf2(pdf_path)
            else:
                print("  ERROR: No PDF library available. Install pdfplumber or PyPDF2")
                return []

            all_content.append({
                'class': class_num,
                'medium': medium,
                'chapters': topics,
                'source': str(pdf_path)
            })
            print(f"    Found {len(topics)} chapters")

        return all_content

    def build_topic_index(self, all_content):
        """Build flat index of all topics in order."""
        index = []
        chapter_id = 0

        for book in sorted(all_content, key=lambda x: x['class']):
            class_num = book['class']
            medium = book['medium']
            chapters = book['chapters']

            for chapter in chapters:
                chapter_id += 1
                chapter_name = chapter['chapter']
                topics = chapter['topics']

                for topic_idx, topic_text in enumerate(topics):
                    index.append({
                        'id': chapter_id * 1000 + topic_idx,
                        'class': class_num,
                        'medium': medium,
                        'chapter': chapter_name,
                        'topic_idx': topic_idx,
                        'topic': topic_text,
                        'source': book['source']
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
        print(f"Saved {len(index)} topics to {path}")
        return index


if __name__ == "__main__":
    from pdf_downloader import PDFDownloader

    downloader = PDFDownloader()
    pdfs = downloader.get_available_pdfs()

    extractor = PDFExtractor()
    all_content = extractor.extract_all(pdfs)
    index = extractor.build_topic_index(all_content)
    extractor.save_index(index)