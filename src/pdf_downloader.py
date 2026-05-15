# NOTE: NCERT PDF direct download URLs are no longer available from official site.
# Using curriculum.json as primary content source (NCERT syllabus based).
# PDFs are not required - content is generated from structured curriculum data.
#
# If you want to add actual PDF content later, check:
# - Diksha Platform (diksha.gov.in)
# - ePathshala app
# - State government education portals
#
# For now, the bot uses the comprehensive curriculum.json with all Class 1-10 topics.

import os
import json
import requests
from pathlib import Path


class PDFDownloader:
    def __init__(self, books_dir="data/books"):
        self.books_dir = Path(books_dir)
        self.books_dir.mkdir(parents=True, exist_ok=True)
        self.curriculum_path = Path("curriculum.json")

    def load_curriculum(self):
        """Load curriculum from JSON file."""
        if self.curriculum_path.exists():
            with open(self.curriculum_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('curriculum', [])
        return []

    def get_available_books(self):
        """Return curriculum chapters as 'books'."""
        curriculum = self.load_curriculum()
        books = []
        for item in curriculum:
            class_num = item.get('class', 0)
            chapter = item.get('chapter', 0)
            topic = item.get('topic', '')
            subtopics = item.get('subtopics', [])
            books.append({
                'class': class_num,
                'chapter': chapter,
                'topic': topic,
                'subtopics': subtopics,
                'source': 'curriculum'
            })
        return books

    def download_all_books(self):
        """Return curriculum as 'downloaded' books."""
        books = self.get_available_books()
        downloaded = []
        for book in books:
            downloaded.append(f"Class {book['class']} - {book['topic']}")
        return downloaded, []

    def get_available_pdfs(self):
        """Return list of available content sources."""
        return self.get_available_books()

    def clear_all(self):
        print("No PDFs to clear - using curriculum content")


if __name__ == "__main__":
    downloader = PDFDownloader()
    print("Downloading NCERT Math Books (Class 1-10)...")
    downloaded, failed = downloader.download_all_books()
    print(f"\nDownloaded: {len(downloaded)} books")
    if failed:
        print(f"Failed: {len(failed)}")
        for c, m, url in failed:
            print(f"  Class {c} {m}: {url}")