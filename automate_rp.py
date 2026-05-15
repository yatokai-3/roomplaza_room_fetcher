import requests
from bs4 import BeautifulSoup
import json
import os

BASE = "https://www.roomplaza.com"

CITIES = {
    "hague": "/en/html/web/search/home?city=4&startDate=2026-08-01&tenants=4",
    "delft": "/en/html/web/search/home?city=3&startDate=2026-08-01&tenants=4",
    "rotterdam": "/en/html/web/search/home?city=1&startDate=2026-08-01&tenants=4"
}


# -------------------- helpers --------------------
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# -------------------- scrape --------------------
def fetch_page(path):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(BASE + path, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    listings = []

    for a in soup.select("a.apartment"):
        apt_id = a.get("data-apartment-id")

        href = a.get("href")
        link = BASE + href if href else None

        caption = a.find("figcaption")

        title = None
        if caption:
            divs = caption.find_all("div")
            if len(divs) > 1:
                title = divs[1].get_text(" ", strip=True)

        price_tag = a.find("div", class_="apartment-price")
        price = price_tag.get_text(strip=True) if price_tag else None

        availability_tag = a.find("span")
        availability = availability_tag.get_text(strip=True) if availability_tag else None

        if apt_id:
            listings.append({
                "id": str(apt_id),
                "link": link,
                "title": title,
                "price": price,
                "availability": availability
            })

    return listings, soup


def get_pages(soup, start_path):
    pages = set([start_path])

    nav = soup.find("nav", class_="pagination")
    if nav:
        for a in nav.find_all("a"):
            href = a.get("href")
            if href and href.startswith("/"):
                pages.add(href)

    return list(pages)


def fetch_all(start_path):
    first, soup = fetch_page(start_path)

    pages = get_pages(soup, start_path)

    all_items = []
    for p in pages:
        items, _ = fetch_page(p)
        all_items.extend(items)

    # dedupe
    return list({x["id"]: x for x in all_items}.values())


# -------------------- per city --------------------
def run_city(city, path):
    FINAL_FILE = f"{city}_final.json"
    SEEN_FILE  = f"{city}_seen_ids.json"

    current = fetch_all(path)

    current_ids = set(x["id"] for x in current)
    seen_ids = set(load_json(SEEN_FILE))

    new_ids = current_ids - seen_ids
    new_list = [x for x in current if x["id"] in new_ids]

    has_new = len(new_ids) > 0

    # update seen_ids (history)
    updated_seen = seen_ids.union(current_ids)
    save_json(SEEN_FILE, list(updated_seen))

    # update final ALWAYS (fresh snapshot)
    save_json(FINAL_FILE, current)

    return {
        "city": city,
        "hasNew": has_new,
        "new": new_list,
        "final": current
    }


# -------------------- main --------------------
def run_once():
    results = []

    for city, path in CITIES.items():
        res = run_city(city, path)
        results.append(res)

    print(json.dumps(results, indent=2,ensure_ascii=False))


if __name__ == "__main__":
    run_once()