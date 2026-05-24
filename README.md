# GemEdge — GeM Bid Scraper & Analyzer

Scrapes awarded Bid/RA listings from the **Government e-Marketplace (GeM)** portal, extracts vendor-level evaluation data, and generates analytical insights.

## What it does

1. **Listing Scraper** — Opens the GeM portal via Playwright, applies filters (Status: Bid/RA, Outcome: Awarded), and collects 30+ bid cards with metadata.
2. **Bid Detail Scraper** — For each bid, fetches the RA result page (financial evaluation) and Bid result page (technical evaluation) using HTTP requests. Extracts L1 winner, prices, ranks, and qualification status.
3. **Evaluation Builder** — Merges financial and technical data into flat vendor-level records. Identifies disqualified vendors and assigns status flags (winner, participated, disqualified).
4. **Data Cleaner** — Normalizes text, cleans prices, handles missing values, removes duplicates, and flags anomalies (zero price, single bidder, suspiciously low bids).
5. **Insights Generator** — Computes competition metrics, L1-L2 price gaps, repeat winner analysis, and disqualification rates.

## Project Structure

```
GEMEDGE/
├── main.py                  # Full pipeline — run this
├── config.py                # Configuration (URL, filters, output paths)
├── requirements.txt         # Python dependencies
├── scraper/
│   ├── listing.py           # Step 1: Scrape bid listings
│   ├── bid_detail.py        # Step 2: Fetch financial + technical data
│   └── evaluation.py        # Step 3: Build vendor evaluation records
├── processor/
│   ├── cleaner.py           # Step 4: Clean and normalize data
│   └── insights.py          # Step 5: Generate analytical insights
└── output/
    ├── bids.csv             # Final cleaned dataset
    ├── bids_full.json       # Full JSON output
    ├── insights.json        # Analysis results
    ├── raw_listings.json    # Intermediate: raw listing data
    ├── enriched_bids.json   # Intermediate: bids with detail data
    └── raw_vendor_records.json  # Intermediate: pre-clean vendor records
```

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
python main.py
```

## Output

- **bids.csv** — One row per vendor per bid, with columns: bid_id, category, buyer, quantity, bid_value, award_date, winner_name, winner_price, num_bidders, vendor_name, vendor_rank, vendor_price, status_flag
- **bids_full.json** — Full JSON with extra fields (remarks, anomaly)
- **insights.json** — Competition stats, price analysis (L1-L2 gap), repeat winners, disqualification rates

## Tech Stack

- **Playwright** — Browser automation for JavaScript-rendered listing pages
- **Requests** — HTTP requests for bid result pages (no JS needed)
- **BeautifulSoup** — HTML parsing and data extraction
- **Pandas** — Data cleaning, transformation, and export
