import os
import json
import requests
from pathlib import Path
from urllib.parse import urljoin

BASE_URL = "https://ncert.nic.in"

# NCERT Class 1-10 book codes (from official website)
# Format: {class: {medium: {subject: pdf_url}}}
NCERT_BOOKS = {
    1: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat1dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt1dd.zip",
    },
    2: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat2dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt2dd.zip",
    },
    3: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat3dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt3dd.zip",
    },
    4: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat4dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt4dd.zip",
    },
    5: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat5dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt5dd.zip",
    },
    6: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat6dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt6dd.zip",
    },
    7: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat7dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt7dd.zip",
    },
    8: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat8dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt8dd.zip",
    },
    9: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat9dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt9dd.zip",
    },
    10: {
        "English": "https://ncert.nic.in/textbook/pdf/lemat10dd.zip",
        "Hindi": "https://ncert.nic.in/textbook/pdf/lhmt10dd.zip",
    },
}


class PDFDownloader:
    def __init__(self, books_dir="data/books"):
        self.books_dir = Path(books_dir)
        self.books_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def download_file(self, url, dest_path, max_retries=3):
        """Download a file with retry logic."""
        for attempt in range(max_retries):
            try:
                print(f"  Downloading: {url}")
                response = requests.get(url, headers=self.headers, timeout=120, stream=True)
                response.raise_for_status()

                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                file_size = dest_path.stat().st_size / (1024 * 1024)
                print(f"  Downloaded: {dest_path.name} ({file_size:.1f} MB)")
                return True
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
        return False

    def download_all_books(self):
        """Download all NCERT math books for Class 1-10."""
        downloaded = []
        failed = []

        for class_num in range(1, 11):
            if class_num not in NCERT_BOOKS:
                continue

            for medium, url in NCERT_BOOKS[class_num].items():
                # Try direct PDF first, then ZIP
                pdf_url = url.replace('.zip', '.pdf')
                dest_name = f"class{class_num}_{medium.lower()}.pdf"
                dest_path = self.books_dir / dest_name

                if dest_path.exists():
                    print(f"  Already exists: {dest_name}")
                    downloaded.append(str(dest_path))
                    continue

                # Try PDF direct
                success = self.download_file(pdf_url, dest_path)
                if not success:
                    # Try ZIP
                    success = self.download_file(url, dest_path.with_suffix('.zip'))
                    if success:
                        # Extract ZIP
                        import zipfile
                        zip_path = dest_path.with_suffix('.zip')
                        if zip_path.exists():
                            try:
                                with zipfile.ZipFile(zip_path, 'r') as zf:
                                    # Extract PDF from zip
                                    for name in zf.namelist():
                                        if name.endswith('.pdf'):
                                            zf.extract(name, self.books_dir)
                                            extracted = self.books_dir / name
                                            extracted.rename(dest_path)
                                            break
                                zip_path.unlink()
                            except Exception as e:
                                print(f"  Extract failed: {e}")

                if dest_path.exists() and dest_path.stat().st_size > 10000:
                    downloaded.append(str(dest_path))
                else:
                    failed.append((class_num, medium, url))

        return downloaded, failed

    def get_available_pdfs(self):
        """Return list of downloaded PDF paths."""
        return list(self.books_dir.glob("*.pdf"))

    def clear_all(self):
        """Delete all downloaded PDFs."""
        for f in self.books_dir.glob("*.pdf"):
            f.unlink()
        print(f"Cleared all PDFs from {self.books_dir}")


if __name__ == "__main__":
    downloader = PDFDownloader()
    print("Downloading NCERT Math Books (Class 1-10)...")
    downloaded, failed = downloader.download_all_books()
    print(f"\nDownloaded: {len(downloaded)} books")
    if failed:
        print(f"Failed: {len(failed)}")
        for c, m, url in failed:
            print(f"  Class {c} {m}: {url}")