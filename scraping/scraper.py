import requests
from bs4 import BeautifulSoup
import json
import os
import time

BASE_URL = "https://www.cs.purdue.edu/academic-programs/courses/2026_spring_courses.html"
ROOT_URL = "https://selfservice.mypurdue.purdue.edu"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Have data folder
os.makedirs("data", exist_ok=True)
# Get course list
print("Fetching the Purdue CS 2026 course list page...")
response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")
# collect all links from root
course_links = []
for a in soup.select("a[href*='bzwsrch.p_catalog_detail']"):
    text = a.get_text(strip=True)
    href = a["href"]
    full_url = href if href.startswith("http") else ROOT_URL + href
    course_links.append({"course_code": text, "url": full_url})

print(f" We have {len(course_links)} CS courses to scrape.\n")

# scrape each pag
data = []

def extract_after(soup_obj, label):
    """Helper to get the <td> text following a label like 'Offered By:'."""
    el = soup_obj.find(string=lambda t: t and label in t)
    if el:
        next_el = el.find_next("td")
        return next_el.get_text(strip=True) if next_el else el.strip()
    return "N/A"

for idx, course in enumerate(course_links, start=1):
    print(f"[{idx}/{len(course_links)}] Scraping {course['course_code']} ...")

    try:
        page = requests.get(course["url"], headers=HEADERS, timeout=25)
        page.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f" Skipping {course['course_code']}: {e}")
        continue

    s = BeautifulSoup(page.text, "html.parser")

    # JSON structure
    title_tag = s.find("th", class_="ddtitle")
    if not title_tag:
        title_tag = s.find("h1") or s.find("caption") or s.find("td", class_="nttitle")
    title = title_tag.get_text(strip=True) if title_tag else "N/A"

    credit_tag = s.find(string=lambda t: "Credit Hours" in t)
    credits = credit_tag.split("Credit Hours:")[-1].strip() if credit_tag else "N/A"

    desc_tag = credit_tag.find_next("td") if credit_tag else None
    description = desc_tag.get_text(strip=True) if desc_tag else "N/A"

   # Academic info
    offered_by = extract_after(s, "Offered By:")
    department = extract_after(s, "Department:")
    levels = extract_after(s, "Levels:")
    schedule_types = extract_after(s, "Schedule Types:")
    prerequisites = extract_after(s, "Prerequisites:")

    # Keep the record
    data.append({
        "course_code": course["course_code"],
        "title": title,
        "credits": credits,
        "description": description,
        "offered_by": offered_by,
        "department": department,
        "levels": levels,
        "schedule_types": schedule_types,
        "prerequisites": prerequisites,
        "url": course["url"]
    })

    print(f" {course['course_code']} scraped successfully.\n")
    time.sleep(1.5)  

# saved structure
json_path = "data/cs_courses_2026_westlafayette.json"
with open(json_path, "w") as f:
    json.dump(data, f, indent=2)

print("\n JSON data saved to:", json_path)
print(f" Scraped {len(data)} courses in total.")

# Print a small sample
if data:
    print("\n Example entry:")
    print(json.dumps(data[0], indent=2))