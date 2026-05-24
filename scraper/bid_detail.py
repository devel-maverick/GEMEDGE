import requests
from bs4 import BeautifulSoup
import re
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def get_bid_details(bids):
    enriched = []

    for bid in bids:
        record = dict(bid)

        url = bid.get('ra_result_url') or bid.get('bid_result_url')
        if url:
            fin = fetch_financial(url)
            if fin:
                record.update(fin)

        bid_url = bid.get('bid_result_url')
        if bid_url:
            tech = fetch_technical(bid_url)
            if tech:
                record['num_bidders'] = tech['num_bidders']
                record['vendors_technical'] = tech['vendors']

        enriched.append(record)
        time.sleep(1)

    print(f"Enriched {len(enriched)} bids")
    return enriched


def fetch_financial(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'lxml')
        table = find_table(soup, required_cols=["Rank", "Total Price"])
        if not table:
            return None

        vendors = []
        rows = table.select("tbody tr") or table.select("tr")[1:]
        for row in rows:
            cells = row.select("td")
            if len(cells) < 4:
                continue
            name = get_seller_name(row, cells)
            price = clean_price(cells[-2].get_text(strip=True))
            rank = cells[-1].get_text(strip=True)
            vendors.append({'vendor_name': name, 'vendor_price': price, 'vendor_rank': rank})

        if not vendors:
            return None

        winner = next((v for v in vendors if v['vendor_rank'] == 'L1'), vendors[0])
        award_date = get_end_date(soup)

        return {
            'winner_name': winner['vendor_name'],
            'winner_price': winner['vendor_price'],
            'bid_value': winner['vendor_price'],
            'award_date': award_date,
            'num_qualified_financial': len(vendors),
            'vendors_financial': vendors,
        }
    except Exception:
        return None


def fetch_technical(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'lxml')
        table = find_table(soup, required_cols=["Status", "Seller Name"])
        if not table:
            return None

        headers = [th.get_text(strip=True) for th in table.select("th")]
        emd_idx = next((i for i, h in enumerate(headers) if "EMD" in h), None)

        vendors = []
        rows = table.select("tbody tr") or table.select("tr")[1:]
        for row in rows:
            cells = row.select("td")
            if len(cells) < 3:
                continue
            name = get_seller_name(row, cells)
            status_span = cells[-1].select_one("span")
            status = status_span.get_text(strip=True) if status_span else cells[-1].get_text(strip=True)
            remarks = cells[emd_idx].get_text(strip=True) if emd_idx is not None and emd_idx < len(cells) else ""
            if remarks == "-":
                remarks = ""
            vendors.append({'vendor_name': name, 'status': status, 'remarks': remarks})

        return {'num_bidders': len(vendors), 'vendors': vendors}
    except Exception:
        return None


def find_table(soup, required_cols):
    for t in soup.select("table"):
        headers = [th.get_text(strip=True) for th in t.select("th")]
        if all(col in headers for col in required_cols):
            return t
    return None


def get_seller_name(row, cells):
    tag = row.select_one("td.sellername span.cid")
    if tag:
        return tag.get_text(strip=True)
    raw = cells[1].get_text(strip=True) if len(cells) > 1 else "N/A"
    raw = re.sub(r'Under PMA.*$', '', raw)
    raw = re.sub(r'\(MSE.*?\)', '', raw)
    raw = re.sub(r'\(MII.*?\)', '', raw)
    return raw.strip()


def clean_price(text):
    text = text.replace('`', '').replace('₹', '').replace('(Bid Price)', '')
    return text.strip()


def get_end_date(soup):
    section = soup.select_one("#collapseOne")
    if not section:
        return "N/A"
    tag = section.find("strong", string=lambda t: t and "End Date / Time" in t)
    if not tag:
        tag = section.find("strong", string=lambda t: t and "End Date" in t and "Validity" not in t)
    if tag:
        span = tag.find_next("span")
        if span:
            return span.get_text(strip=True)
    return "N/A"


