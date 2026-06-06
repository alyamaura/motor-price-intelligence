"""Motor Price Intelligence - OLX Scraper"""

import os
import sys
import time
import random
import httpx
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv

# Import dari folder yang sama
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cleaner import (
    normalize_brand, normalize_model, parse_price,
    parse_year, parse_mileage, is_valid_listing
)

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
]

SEARCH_TARGETS = [
    ("honda", "beat"), ("honda", "vario 160"), ("honda", "pcx 160"),
    ("honda", "scoopy"), ("honda", "adv 160"),
    ("yamaha", "nmax"), ("yamaha", "aerox"), ("yamaha", "mio"),
    ("yamaha", "freego"), ("yamaha", "r15"),
    ("suzuki", "gsx"), ("kawasaki", "ninja 250"), ("kawasaki", "klx"),
]


def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    }


def scrape_olx_search(brand, model_query, max_pages=2):
    results = []
    query = f"{brand}+{model_query.replace(' ', '+')}"

    for page in range(1, max_pages + 1):
        url = f"https://www.olx.co.id/motor_c198?q={query}&page={page}"
        print(f"  Fetching: {url}")

        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                response = client.get(url, headers=get_headers())

            if response.status_code != 200:
                print(f"  Status {response.status_code}, skip")
                break

            soup = BeautifulSoup(response.text, 'lxml')
            items = soup.find_all('li', {'data-aut-id': 'itemBox'})
            if not items:
                items = soup.find_all('article')

            for item in items:
                try:
                    title_el = (
                        item.find(['span', 'p'], {'data-aut-id': 'itemTitle'}) or
                        item.find('h2') or item.find('h3')
                    )
                    price_el = item.find(['span', 'p'], {'data-aut-id': 'itemPrice'})
                    loc_el   = item.find(['span', 'p'], {'data-aut-id': 'item-location'})
                    link_el  = item.find('a', href=True)

                    title      = title_el.get_text(strip=True) if title_el else ""
                    price_text = price_el.get_text(strip=True) if price_el else ""
                    loc_text   = loc_el.get_text(strip=True) if loc_el else ""
                    item_url   = link_el['href'] if link_el else ""
                    if item_url and not item_url.startswith('http'):
                        item_url = "https://www.olx.co.id" + item_url

                    parsed_price   = parse_price(price_text)
                    parsed_year    = parse_year(title)
                    parsed_mileage = parse_mileage(title)
                    norm_brand     = normalize_brand(f"{brand} {title}")
                    norm_model     = normalize_model(f"{model_query} {title}")
                    city           = loc_text.split(',')[0].strip() if ',' in loc_text else loc_text.strip()

                    if not is_valid_listing(norm_brand, norm_model, parsed_year, parsed_price):
                        continue

                    results.append({
                        "source_url": item_url,
                        "source_platform": "olx",
                        "brand": norm_brand,
                        "model": norm_model,
                        "year": parsed_year,
                        "price": parsed_price,
                        "mileage_km": parsed_mileage,
                        "location_city": city,
                        "condition_notes": title[:200],
                        "is_active": True,
                        "is_valid": True,
                    })
                except Exception as e:
                    continue

            print(f"  Halaman {page}: {len(results)} valid sejauh ini")
            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"  Error: {e}")
            break

    return results


def save_to_supabase(listings):
    if not listings:
        return 0
    saved = 0
    for i in range(0, len(listings), 50):
        batch = listings[i:i+50]
        try:
            supabase.table("motor_listings").upsert(
                batch, on_conflict="source_url"
            ).execute()
            saved += len(batch)
        except Exception as e:
            print(f"  Save error: {e}")
    return saved


def main():
    print("=" * 50)
    print("Motor Price Intelligence - Scraper")
    print("=" * 50)

    total = 0
    for brand, model_query in SEARCH_TARGETS:
        print(f"\n[{brand.upper()}] {model_query}")
        listings = scrape_olx_search(brand, model_query)
        saved = save_to_supabase(listings)
        total += saved
        print(f"  Tersimpan: {saved}")
        time.sleep(random.uniform(5, 10))

    print(f"\nTotal tersimpan: {total}")


if __name__ == "__main__":
    main()