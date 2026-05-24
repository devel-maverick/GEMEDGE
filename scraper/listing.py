from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from config import BASE_URL, HEADLESS, TIMEOUT, MIN_BIDS

BASE = "https://bidplus.gem.gov.in"


def get_bid_listings():
    bids = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()

        page.goto(BASE_URL, timeout=TIMEOUT)
        page.wait_for_timeout(5000)
        page.click('#bidrastatus')
        page.wait_for_timeout(3000)
        page.click('#bid_awarded')
        page.wait_for_timeout(4000)

        while len(bids) < MIN_BIDS:
            soup = BeautifulSoup(page.content(), 'lxml')
            for c in soup.select('div.card'):
                bid = extract_bid(c)
                if bid and bid['bid_id'] not in seen:
                    seen.add(bid['bid_id'])
                    bids.append(bid)

            if len(bids) >= MIN_BIDS:
                break

            next_btn = page.query_selector("a.page-link.next")
            if not next_btn:
                break
            next_btn.click()
            page.wait_for_timeout(4000)

        browser.close()

    print(f"Scraped {len(bids)} bids")
    return bids


def extract_bid(card):
    try:
        bid_id = "N/A"
        ra_id = None
        for link in card.select('a.bid_no_hover'):
            href = link.get('href', '')
            if 'showbidDocument' in href:
                bid_id = link.text.strip()
            elif 'showradocument' in href:
                ra_id = link.text.strip()

        category = "N/A"
        items_tag = find_label(card, "Items")
        if items_tag:
            a_tag = items_tag.find_next_sibling("a")
            if a_tag:
                category = a_tag.get("data-content") or a_tag.text.strip()

        buyer = "N/A"
        dept_tag = find_label(card, "Department")
        if dept_tag:
            next_div = dept_tag.parent.find_next_sibling("div", class_="row")
            if next_div:
                buyer = next_div.get_text(separator=", ", strip=True)

        quantity = "N/A"
        qty_tag = find_label(card, "Quantity")
        if qty_tag and qty_tag.next_sibling:
            quantity = qty_tag.next_sibling.strip().lstrip(":").strip()

        start = card.select_one("span.start_date")
        end = card.select_one("span.end_date")

        bid_result_url = None
        ra_result_url = None
        for link in card.select("a[href*='getBidResultView']"):
            href = link.get('href', '')
            if not href.startswith('http'):
                href = BASE + href
            btn = link.select_one("input[type='button']")
            if btn and 'RA' in btn.get('value', ''):
                ra_result_url = href
            else:
                bid_result_url = href

        return {
            'bid_id': bid_id,
            'ra_id': ra_id,
            'category': category,
            'buyer': buyer,
            'quantity': quantity,
            'start_date': start.text.strip() if start else "N/A",
            'end_date': end.text.strip() if end else "N/A",
            'bid_result_url': bid_result_url,
            'ra_result_url': ra_result_url,
        }
    except Exception:
        return None


def find_label(card, label):
    return card.find("strong", string=lambda t: t and label in t)
