import os
import requests
from pathlib import Path

def download_file(url, output_path):
    print(f"Downloading {url} to {output_path}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"✅ Successfully downloaded to {output_path}")
            return True
        else:
            print(f"❌ Failed to download, status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
    return False

def main():
    books_dir = Path("data/books/class_10")
    books_dir.mkdir(parents=True, exist_ok=True)
    
    # Official public domain GED Mathematical Reasoning Formula Sheet containing Pythagoras, area, volume, and algebra
    url = "https://www.ged.com/wp-content/uploads/math_formula_sheet-1-1.pdf"
    output_path = books_dir / "class_10_math_formulas.pdf"
    
    success = download_file(url, output_path)
    if success:
        print("Formula book / PDF downloaded successfully and placed in data/books/class_10!")
    else:
        print("Could not download mathematical formula PDF. Please check internet connection.")

if __name__ == "__main__":
    main()

