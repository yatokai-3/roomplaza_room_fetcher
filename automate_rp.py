import requests
from bs4 import BeautifulSoup
import json, os

#using smtp now. . . . . 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



BASE = "https://www.roomplaza.com"
CITIES = {
    "hague":     "/en/html/web/search/home?city=4&startDate=2026-08-01&tenants=4",
    "delft":     "/en/html/web/search/home?city=3&startDate=2026-08-01&tenants=4",
    "rotterdam": "/en/html/web/search/home?city=1&startDate=2026-08-01&tenants=4",
    "hague_3":      "/en/html/web/search/home?city=4&startDate=2026-08-01&tenants=3",
    "delft_3":      "/en/html/web/search/home?city=3&startDate=2026-08-01&tenants=3",
    "rotterdam_3":  "/en/html/web/search/home?city=1&startDate=2026-08-01&tenants=3"
}
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- helpers ----------
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def highlight_diff(old, new):
    if old == new:
        return new
    # find common prefix and suffix
    i = 0
    while i < len(old) and i < len(new) and old[i] == new[i]:
        i += 1
    j = 0
    while j < len(old) and j < len(new) and old[-(j+1)] == new[-(j+1)]:
        j += 1
    changed_part = new[i: len(new)-j if j else len(new)]
    if not changed_part.strip():
        return new
    return (
        new[:i] +
        f"<span style='color:red;font-weight:bold;text-decoration:underline'>{changed_part}</span>" +
        (new[len(new)-j:] if j else "")
    )


# ---------- scrape ----------
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
            listings.append({"id": str(apt_id), "link": link,
                              "title": title, "price": price,
                              "availability": availability})
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
    return list({x["id"]: x for x in all_items}.values())

# ---------- email ----------
# def build_html(all_new):
#     if not all_new:
#         return None
#     rows = ""
#     for city, listings in all_new.items():
#         if not listings:
#             continue
#         rows += f"<h3 style='color:#5534B7;margin:20px 0 8px'>{city.title()} — {len(listings)} new</h3>"
#         for l in listings:
#             rows += f"""
#             <div style='border:1px solid #ddd;border-radius:8px;padding:12px 16px;margin-bottom:10px'>
#               <b>{l['title'] or 'No title'}</b><br>
#               <span style='color:#888'>{l['price']} · {l['availability']}</span><br>
#               <a href='{l['link']}' style='color:#5534B7'>View listing →</a>
#             </div>"""
#     return f"""
#     <div style='font-family:sans-serif;max-width:600px;margin:auto'>
#       <h2 style='color:#222'>🏠 New RoomPlaza listings</h2>
#       {rows}
#       <p style='color:#aaa;font-size:12px'>Auto-sent by your GitHub Actions scraper</p>
#     </div>"""



# def send_email(all_new):
#     total = sum(len(v) for v in all_new.values())
    
#     if total == 0:                              # ← check BEFORE building html
#         print("No new listings — skipping email.")
#         return
    
#     html = build_html(all_new)
#     gmail_user     = os.environ["GMAIL_USER"]
#     gmail_password = os.environ["GMAIL_APP_PASS"]
#     notify_email   = os.environ["NOTIFY_EMAIL"]
#     cc_emails      = [x for x in os.environ.get("CC_EMAILS", "").split(",") if x]

#     msg = MIMEMultipart("alternative")
#     msg["Subject"] = f"🏠 {total} new RoomPlaza listing(s)!"
#     msg["From"]    = gmail_user
#     msg["To"]      = notify_email
#     if cc_emails:
#         msg["Cc"]  = ", ".join(cc_emails)
#     msg.attach(MIMEText(html, "html"))

#     all_recipients = [notify_email] + cc_emails
#     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
#         smtp.login(gmail_user, gmail_password)
#         smtp.sendmail(gmail_user, all_recipients, msg.as_string())
#     print(f"Email sent to {all_recipients}")

def build_html(all_new):
    rows = ""
    for city, data in all_new.items():
        new_listings     = data["new"]
        changed_listings = data["changed"]
        if not new_listings and not changed_listings:
            continue
        if new_listings:
            rows += f"<h3 style='color:#5534B7;margin:20px 0 8px'>{city.title()} — {len(new_listings)} new</h3>"
            for l in new_listings:
                rows += f"""
                <div style='border:1px solid #ddd;border-radius:8px;padding:12px 16px;margin-bottom:10px'>
                  <b>{l['title'] or 'No title'}</b><br>
                  <span style='color:#888'>{l['price']} · {l['availability']}</span><br>
                  <a href='{l['link']}' style='color:#5534B7'>View listing →</a>
                </div>"""
        if changed_listings:
            rows += f"<h3 style='color:#E07B00;margin:20px 0 8px'>{city.title()} — {len(changed_listings)} updated</h3>"
            for l in changed_listings:
                rows += f"""
                <div style='border:1px solid #f0c080;border-radius:8px;padding:12px 16px;margin-bottom:10px'>
                  <b>{l['title'] or 'No title'}</b><br>
                  <span style='color:#888'>{l['price']} · {l['availability']}</span><br>
                  <span style='color:#aaa;font-size:12px'>{l.get('_change', '')}</span><br>
                  <a href='{l['link']}' style='color:#5534B7'>View listing →</a>
                </div>"""
    return f"""
    <div style='font-family:sans-serif;max-width:600px;margin:auto'>
      <h2 style='color:#222'>🏠 RoomPlaza update</h2>
      {rows}
      <p style='color:#aaa;font-size:12px'>Auto-sent by your GitHub Actions scraper</p>
    </div>"""

def send_email(all_new):
    total_new     = sum(len(v["new"])     for v in all_new.values())
    total_changed = sum(len(v["changed"]) for v in all_new.values())
    if total_new == 0 and total_changed == 0:
        print("No new or changed listings — skipping email.")
        return
    html = build_html(all_new)
    gmail_user     = os.environ["GMAIL_USER"]
    gmail_password = os.environ["GMAIL_APP_PASS"]
    notify_email   = os.environ["NOTIFY_EMAIL"]
    cc_emails      = [x for x in os.environ.get("CC_EMAILS", "").split(",") if x]
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🏠 {total_new} new · {total_changed} updated RoomPlaza listing(s)!"
    msg["From"]    = gmail_user
    msg["To"]      = notify_email
    if cc_emails:
        msg["Cc"]  = ", ".join(cc_emails)
    msg.attach(MIMEText(html, "html"))
    all_recipients = [notify_email] + cc_emails
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_password)
        smtp.sendmail(gmail_user, all_recipients, msg.as_string())
    print(f"Email sent — {total_new} new, {total_changed} updated")

# ---------- per city ----------
# def run_city(city, path):
#     seen_file  = os.path.join(DATA_DIR, f"{city}_seen_ids.json")
#     final_file = os.path.join(DATA_DIR, f"{city}_final.json")
#     current    = fetch_all(path)
#     current_ids = set(x["id"] for x in current)
#     seen_ids    = set(load_json(seen_file))
#     new_ids     = current_ids - seen_ids
#     new_list    = [x for x in current if x["id"] in new_ids]

#     # sort by price low to high
#     def parse_price(listing):
#         try:
#             return int(''.join(filter(str.isdigit, listing["price"] or "")))
#         except:
#             return 99999   # push unparseable prices to bottom
#     new_list.sort(key=parse_price)
    
#     save_json(seen_file,  list(seen_ids.union(current_ids)))
#     save_json(final_file, current)
#     return new_list
def run_city(city, path):
    seen_file   = os.path.join(DATA_DIR, f"{city}_seen_ids.json")
    final_file  = os.path.join(DATA_DIR, f"{city}_final.json")
    current     = fetch_all(path)
    current_ids = set(x["id"] for x in current)
    seen_ids    = set(load_json(seen_file))
    prev_final  = {x["id"]: x for x in load_json(final_file)}  # ← load previous snapshot

    new_ids      = current_ids - seen_ids
    new_list     = [x for x in current if x["id"] in new_ids]

    # check for changed listings
    changed_list = []
    for x in current:
        if x["id"] in prev_final:
            prev = prev_final[x["id"]]
            if (x["title"] != prev["title"] or x["price"] != prev["price"] or x["availability"] != prev["availability"]):
                
                title_diff = highlight_diff(prev["title"], x["title"])
                price_diff = highlight_diff(prev["price"], x["price"])
                avail_diff = highlight_diff(prev["availability"], x["availability"])

                x["_change"] = f"""
                    <b>Title:</b> {title_diff}<br>
                    <b>Price:</b> {price_diff}<br>
                    <b>Availability:</b> {avail_diff}<br>
                    <span style='color:#aaa;font-size:11px'>
                        was: {prev['title']} · {prev['price']} · {prev['availability']}
                    </span>
                """
                changed_list.append(x)
                
                  
                # x["_change"] = f"was: {prev['price']} · {prev['availability']}"
                # x["_change"] = (f"Title was: {prev['title']}<br>"if x["title"].strip() != prev["title"].strip() else "") + f"was: {prev['price']} · {prev['availability']}"
                # changed_list.append(x)

    def parse_price(listing):
        try:
            return int(''.join(filter(str.isdigit, listing["price"] or "")))
        except:
            return 99999

    new_list.sort(key=parse_price)
    changed_list.sort(key=parse_price)

    save_json(seen_file,  list(seen_ids.union(current_ids)))
    save_json(final_file, current)
    return {"new": new_list, "changed": changed_list}

# ------------------------------WHAT I CHANGED-----------------


# ---------- main ----------
def run_once():
    all_new = {}
    for city, path in CITIES.items():
        print(f"Checking {city}...")
        all_new[city] = run_city(city, path)
    send_email(all_new)

if __name__ == "__main__":
    run_once()

