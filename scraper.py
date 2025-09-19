import requests
from bs4 import BeautifulSoup
import os
import json
import time

LIBRARY_PATH = "Library"
READING_LIST_FILE = "readinglist.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def load_metadata(book_path):
    meta_file = os.path.join(book_path, "metadata.json")
    if os.path.exists(meta_file):
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"chapters": []}

def save_metadata(book_path, metadata):
    with open(os.path.join(book_path, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
 
def load_reading_list():
    reading_list = {}
    if not os.path.exists(READING_LIST_FILE):
        print(f"No {READING_LIST_FILE} found. Please create one with 'Title,URL' lines.")
        return reading_list

    with open(READING_LIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line:
                continue
            title, url = line.split(",", 1)
            title, url = title.strip(), url.strip()
            if title in reading_list:
                print(f"Duplicate entry for '{title}' found in {READING_LIST_FILE}, skipping duplicate.")
                continue
            reading_list[title] = url
    return reading_list

def scrape_book(title, url):
    print(f"\nChecking {title}")
    book_path = os.path.join(LIBRARY_PATH, title)
    os.makedirs(book_path, exist_ok=True)

    metadata = load_metadata(book_path)
    known_chapters = {c["url"] for c in metadata["chapters"]}

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    toc_rows = soup.select("table tbody tr.chapter-row")
    print(f"  Found {len(toc_rows)} rows in TOC")

    new_chapters = []
    for row in toc_rows:
        link = row.select_one("a[href]")
        if not link:
            continue

        chapter_url = "https://www.royalroad.com" + link["href"]
        chapter_title = link.get_text(strip=True)

        if chapter_url not in known_chapters:
            new_chapters.append((chapter_title, chapter_url))

    if not new_chapters:
        print("No new chapters found.")
        return

    for chapter_title, chapter_url in new_chapters:
        print(f"Downloading {chapter_title}")

        cr = requests.get(chapter_url, headers=HEADERS)
        csoup = BeautifulSoup(cr.text, "html.parser")

        content_elem = csoup.select_one(".chapter-content")
        if not content_elem:
            print("Could not find content.")
            continue

        content = content_elem.get_text("\n", strip=True)

        safe_title = "".join(x for x in chapter_title if x.isalnum() or x in " _-")
        filename = os.path.join(book_path, f"{safe_title}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        metadata["chapters"].append({
            "title": chapter_title,
            "url": chapter_url,
            "read": False
        })

        save_metadata(book_path, metadata)
        time.sleep(3)

def main():
    os.makedirs(LIBRARY_PATH, exist_ok=True)
    reading_list = load_reading_list()
    for title, url in reading_list.items():
        scrape_book(title, url)

if __name__ == "__main__":
    main()
