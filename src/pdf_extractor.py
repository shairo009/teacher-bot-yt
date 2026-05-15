# PDF Extractor - Now uses curriculum.json
# Since NCERT official PDFs are not directly accessible,
# we parse the curriculum.json structure as our content source.

import os
import json
from pathlib import Path


class PDFExtractor:
    """Extract topics from curriculum.json instead of PDF files."""

    def __init__(self, books_dir="data/books"):
        self.books_dir = Path(books_dir)
        self.curriculum_path = Path("curriculum.json")
        self.all_content = []

    def load_curriculum(self):
        """Load curriculum from JSON file."""
        if self.curriculum_path.exists():
            with open(self.curriculum_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('curriculum', [])
        return []

    def extract_all(self, book_list=None):
        """Extract content from curriculum (no actual PDFs needed)."""
        curriculum = self.load_curriculum()

        all_content = []
        for item in curriculum:
            class_num = item.get('class', 0)
            chapter_num = item.get('chapter', 0)
            topic = item.get('topic', '')
            subtopics = item.get('subtopics', [])

            # Group by chapter
            chapters = []
            chapter_data = {
                'chapter': f"Chapter {chapter_num}: {topic}",
                'topics': subtopics
            }
            chapters.append(chapter_data)

            all_content.append({
                'class': class_num,
                'medium': 'English',  # Default medium
                'chapters': chapters,
                'source': 'curriculum'
            })
            print(f"  Class {class_num}, Chapter {chapter_num}: {topic} ({len(subtopics)} subtopics)")

        return all_content

    def build_topic_index(self, all_content):
        """Build flat index of all topics in order."""
        index = []
        topic_id = 0

        for book in sorted(all_content, key=lambda x: x['class']):
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
                        'topic': topic_text,
                        'source': 'curriculum'
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
    extractor = PDFExtractor()
    print("Extracting content from curriculum...")
    all_content = extractor.extract_all()
    print(f"\nExtracted {len(all_content)} classes")
    index = extractor.build_topic_index(all_content)
    extractor.save_index(index)
    print(f"\nTotal topics: {len(index)}")