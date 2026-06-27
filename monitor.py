import os
import sys
import json
import re
import requests
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "products_db.json")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "dubey_laptop_alerts_2026")

def send_notification(title, message, link, priority="default", tags="computer"):
    print(f"Sending notification: {title} - {message}")
    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    headers = {
        "Title": title.encode("utf-8").decode("latin-1"),
        "Priority": priority,
        "Tags": tags,
    }
    if link:
        headers["Click"] = link
        
    try:
        r = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=10)
        print(f"Notification sent successfully: Status {r.status_code}")
    except Exception as e:
        print(f"Failed to send notification: {e}")

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
    return {"lenovo": {}, "asus": {}}

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2)
        print("Database updated successfully.")
    except Exception as e:
        print(f"Error saving database: {e}")

def scrape_asus():
    url = "https://www.asus.com/in/deals/outlet/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    
    print(f"Fetching Asus Outlet: {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"Failed to fetch Asus Outlet: Status {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.content, "html.parser")
        containers = []
        for tag in soup.find_all(class_=True):
            cls_str = " ".join(tag.get('class'))
            if 'productCardContainer' in cls_str:
                containers.append(tag)
                
        products = []
        for card in containers:
            name_tag = None
            heading_div = None
            for d in card.find_all("div", class_=True):
                if 'headingRow' in " ".join(d.get('class')):
                    heading_div = d
                    break
            if heading_div:
                name_tag = heading_div.find("a")
            if not name_tag:
                name_tag = card.find("a")
                
            name = name_tag.get_text(strip=True) if name_tag else "Unknown Asus Laptop"
            link = name_tag.get('href') if name_tag else ""
            if link and not link.startswith("http"):
                link = "https://www.asus.com" + link
                
            part_div = None
            for d in card.find_all("div", class_=True):
                if 'partNumber' in " ".join(d.get('class')):
                    part_div = d
                    break
            part_no = ""
            if part_div:
                part_no = part_div.get_text(strip=True).replace("Part Number:", "").strip()
            else:
                part_match = re.search(r'Part Number:\s*([a-zA-Z0-9_\-]+)', card.get_text())
                if part_match:
                    part_no = part_match.group(1)
                    
            card_text = card.get_text("\n")
            rupee_matches = re.findall(r'₹\s*([0-9,.]+)', card_text)
            
            price_current = ""
            price_original = ""
            if len(rupee_matches) >= 1:
                price_current = "Rs. " + rupee_matches[0]
            if len(rupee_matches) >= 2:
                price_original = "Rs. " + rupee_matches[1]
                
            status = "Out of Stock"
            if "buy" in card_text.lower():
                status = "In Stock"
            elif "notify me" in card_text.lower():
                status = "Out of Stock"
                
            if part_no:
                products.append({
                    "name": name,
                    "part_number": part_no,
                    "price_current": price_current,
                    "price_original": price_original,
                    "link": link,
                    "status": status
                })
        return products
    except Exception as e:
        print(f"Error scraping Asus: {e}")
        return []

async def scrape_lenovo():
    url = "https://www.lenovo.com/in/outletin/en/laptops/"
    print(f"Launching Playwright to fetch Lenovo Outlet: {url}...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
            except Exception as e:
                print(f"Navigation timed out or errored: {e}, proceeding with current DOM.")
                
            # Allow page JS to execute and hydrate products
            await asyncio.sleep(8)
            
            content = await page.content()
            await browser.close()
            
        soup = BeautifulSoup(content, "html.parser")
        items = soup.find_all(class_=lambda c: c and 'product_item' in c.split())
        
        products = []
        for item in items:
            name = ""
            title_div = item.find(class_=lambda c: c and 'product_title' in c.split())
            if title_div:
                name_tag = title_div.find("a")
                if name_tag:
                    name = name_tag.get_text(strip=True)
            if not name:
                name_tag = item.find("a", class_=lambda c: c and 'lazy_href' in c.split())
                if name_tag:
                    name = name_tag.get_text(strip=True)
                    
            link = ""
            link_tag = item.find("a", href=lambda h: h and '/p/' in h)
            if link_tag:
                link = link_tag['href']
                if link and not link.startswith("http"):
                    link = "https://www.lenovo.com" + link
                    
            price_cur = ""
            price_orig = ""
            price_span = item.find("span", class_=lambda c: c and 'price-title' in c.split())
            if price_span:
                price_cur = price_span.get_text(strip=True).replace("₹", "Rs. ").replace("?", "Rs. ")
                
            del_tag = item.find("del", class_=lambda c: c and 'price' in c.split())
            if del_tag:
                price_orig = del_tag.get_text(strip=True).replace("₹", "Rs. ").replace("?", "Rs. ")
                
            card_text = item.get_text(" ").lower()
            status = "In Stock"
            if "out of stock" in card_text or "temporarily unavailable" in card_text or "notify me" in card_text:
                status = "Out of Stock"
            elif "buy now" in card_text or "add to cart" in card_text or "add to bag" in card_text:
                status = "In Stock"
                
            name = re.sub(r'\s+', ' ', name).strip()
            
            if link:
                part_no = link.split('/')[-1].split('?')[0]
                products.append({
                    "name": name,
                    "part_number": part_no,
                    "price_current": price_cur,
                    "price_original": price_orig,
                    "link": link,
                    "status": status
                })
        return products
    except Exception as e:
        print(f"Error scraping Lenovo: {e}")
        return []

def monitor():
    print(f"Starting monitoring session. Topic: {NTFY_TOPIC}")
    db = load_db()
    
    # 1. Scrape Asus
    asus_products = scrape_asus()
    print(f"Found {len(asus_products)} products on Asus Outlet.")
    
    # 2. Scrape Lenovo
    lenovo_products = asyncio.run(scrape_lenovo())
    print(f"Found {len(lenovo_products)} products on Lenovo Outlet.")
    
    db_changed = False
    
    # Process Asus
    for p in asus_products:
        part = p["part_number"]
        seen_before = part in db["asus"]
        
        if not seen_before:
            # NEW PRODUCT LISTED!
            title = "ASUS Outlet: New Listing! 🚀"
            msg = f"{p['name']}\nPrice: {p['price_current']} (Original: {p['price_original']})\nStatus: {p['status']}"
            send_notification(title, msg, p["link"], priority="high", tags="computer,rocket")
            
            db["asus"][part] = p
            db_changed = True
        else:
            # Check for stock status changes
            old_status = db["asus"][part].get("status", "Out of Stock")
            new_status = p["status"]
            if old_status == "Out of Stock" and new_status == "In Stock":
                # BACK IN STOCK!
                title = "ASUS Outlet: Back in Stock! 🔥"
                msg = f"{p['name']}\nPrice: {p['price_current']} (Original: {p['price_original']})"
                send_notification(title, msg, p["link"], priority="high", tags="computer,fire")
            
            # Update product details
            db["asus"][part] = p
            db_changed = True
            
    # Process Lenovo
    for p in lenovo_products:
        part = p["part_number"]
        seen_before = part in db["lenovo"]
        
        if not seen_before:
            # NEW PRODUCT LISTED!
            title = "Lenovo Outlet: New Listing! 🚀"
            msg = f"{p['name']}\nPrice: {p['price_current']} (Original: {p['price_original']})\nStatus: {p['status']}"
            send_notification(title, msg, p["link"], priority="high", tags="computer,rocket")
            
            db["lenovo"][part] = p
            db_changed = True
        else:
            # Check for stock status changes
            old_status = db["lenovo"][part].get("status", "Out of Stock")
            new_status = p["status"]
            if old_status == "Out of Stock" and new_status == "In Stock":
                # BACK IN STOCK!
                title = "Lenovo Outlet: Back in Stock! 🔥"
                msg = f"{p['name']}\nPrice: {p['price_current']} (Original: {p['price_original']})"
                send_notification(title, msg, p["link"], priority="high", tags="computer,fire")
            
            # Update product details
            db["lenovo"][part] = p
            db_changed = True
            
    if db_changed:
        save_db(db)
    else:
        print("No changes in listings.")
    print("Monitoring session finished.")

if __name__ == "__main__":
    monitor()
