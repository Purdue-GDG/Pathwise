import firebase_admin
from firebase_admin import credentials, firestore
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

BASE_URL = "https://catalog.purdue.edu/content.php?catoid=7&navoid=2928"
ROOT_URL = "https://catalog.purdue.edu"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

OUTPUT_JSON = "data/cs_courses_2026_westlafayette.json"
cred = credentials.Certificate("/Users/nehajain/Downloads/firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ensure data folder exists
os.makedirs("data", exist_ok=True)

def full_url(href: str) -> str:
    if not href:
        return ""
    return href if href.startswith("http") else ROOT_URL + "/" + href.lstrip("/")

def set_query_param(url: str, key: str, value: str) -> str:
    """Return url with key=value set/replaced in the query string."""
    u = urlparse(url)
    q = dict(parse_qsl(u.query, keep_blank_values=True))
    q[key] = str(value)
    new_q = urlencode(q, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_q, u.fragment))

def extract_preview_links_from_soup(soup: BeautifulSoup) -> set:
    links = set()
    for a in soup.select("a[href*='preview_course_nopop.php']"):
        href = a.get("href", "")
        if href:
            links.add(full_url(href))
    return links

def extract_text(soup: BeautifulSoup) -> str:
    return soup.get_text("\n", strip=True)

def extract_course_fields(soup: BeautifulSoup, url: str) -> dict:
    # Prefer structured spans if present
    code_el = soup.select_one("span.coursecode, span.course_code, span.course-code")
    header_el = soup.find(["h1", "h2"])
    header_text = header_el.get_text(" ", strip=True) if header_el else ""

    # course_code
    if code_el:
        course_code = code_el.get_text(strip=True)
    else:
        m = re.search(r"[A-Z&]{2,}\s?\d{3,5}[A-Z]?", header_text)
        course_code = m.group(0) if m else "N/A"

    # title
    title = header_text or "N/A"
    if course_code != "N/A" and title.startswith(course_code):
        # strip code and following delimiters/hyphens
        rest = title[len(course_code):].lstrip(" -–—\xa0")
        title = rest if rest else title

    # credits
    all_text = extract_text(soup)
    m_credit = re.search(r"(Credit(?:s| Hours)?\s*[:\-]?\s*[0-9]+(?:\.[0-9]+)?(?:\s*-\s*[0-9]+(?:\.[0-9]+)?)?)", all_text, re.I)
    credits = m_credit.group(1) if m_credit else "N/A"

    # prerequisites
    m_pr = re.search(r"(Prerequisite[s]?:\s*.*?)(?:\n[A-Z][a-z]+:|\Z)", all_text, re.I | re.S)
    prerequisites = m_pr.group(1).strip() if m_pr else "N/A"

    return {
        "course_code": course_code,
        "title": title,
        "credits": credits,
        "prerequisites": prerequisites,
        "url": url,
    }

def coid_key(url: str) -> str:
    qs = dict(parse_qsl(urlparse(url).query))
    return qs.get("coid", url)

def collect_all_preview_links():
    preview = set()
    page = 1
    while page <= 1:
        url = f"{BASE_URL}&print=1&expand=1&filter%5B3%5D=1&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5Bcpage%5D={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f" Error fetching page {page}: {e}")
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        page_links = extract_preview_links_from_soup(soup)
        new = page_links - preview
        preview |= page_links
        print(f"page {page}: +{len(new)} links (total: {len(preview)})")
        if not page_links or len(new) == 0:
            break
        page += 1
        time.sleep(0.25)
    return preview

# ---- Crawl logic ----
print("Fetching the Purdue catalog base page...")
r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
r.raise_for_status()
base_soup = BeautifulSoup(r.text, "html.parser")

print("Scanning master course listing pages...")
preview_links = collect_all_preview_links()
preview_links = sorted(preview_links)
print(f"\nTotal unique preview links collected: {len(preview_links)}")

# Load existing JSON to support additive writes and dedup
existing_by_coid = {}
if os.path.exists(OUTPUT_JSON):
    try:
        with open(OUTPUT_JSON, "r") as f:
            existing_list = json.load(f)
        for item in existing_list:
            existing_by_coid[coid_key(item.get("url", ""))] = item
        print(f"Loaded {len(existing_by_coid)} existing records from {OUTPUT_JSON}")
    except Exception:
        print("Existing JSON unreadable; starting fresh.")
        existing_by_coid = {}

# Scrape each preview page
total = len(preview_links)
for idx, url in enumerate(preview_links[:5], start=1):
    print(f"[{idx}/{total}] Scraping: {url}")
    try:
        pr = requests.get(url, headers=HEADERS, timeout=30)
        pr.raise_for_status()
    except requests.RequestException as e:
        print(f"  Skipping due to error: {e}")
        continue
    psoup = BeautifulSoup(pr.text, "html.parser")
    record = extract_course_fields(psoup, url)
    existing_by_coid[coid_key(url)] = record

    if idx % 5 == 0 or idx == total:
        print(f"  Progress: saved {idx}/{total} (current unique records: {len(existing_by_coid)})")
    time.sleep(0.2)

# Write combined results
final_list = sorted(existing_by_coid.values(), key=lambda x: (x.get("course_code", ""), x.get("title", "")))
with open(OUTPUT_JSON, "w") as f:
    json.dump(final_list, f, indent=2)


print(f"\n Saved {len(final_list)} total courses to: {OUTPUT_JSON}")
courses_ref = db.collection("courses")
count = 0

for course in final_list:
    # Use course_code as the Firestore doc ID
    doc_id = course.get("course_code", "UNKNOWN").replace(" ", "_").replace("/", "_")

    courses_ref.document(doc_id).set(course)
    count += 1

print(f"Uploaded {count} courses to Firestore.")