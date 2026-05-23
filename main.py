import os
import json
import pandas as pd
from config import OUTPUT_DIR, OUTPUT_FILE
from scraper.listing import get_bid_listings
from scraper.bid_detail import get_bid_details
from scraper.evaluation import get_evaluation_details
from processor.cleaner import clean_data
from processor.insights import generate_insights


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    bids = get_bid_listings()
    save_json(bids, os.path.join(OUTPUT_DIR, "raw_listings.json"))

    enriched = get_bid_details(bids)
    save_json(enriched, os.path.join(OUTPUT_DIR, "enriched_bids.json"))

    vendor_records = get_evaluation_details(enriched)
    save_json(vendor_records, os.path.join(OUTPUT_DIR, "raw_vendor_records.json"))

    df = clean_data(vendor_records)

    export_cols = [
        'bid_id', 'category', 'buyer', 'quantity', 'bid_value', 'award_date',
        'winner_name', 'winner_price', 'num_bidders', 'vendor_name',
        'vendor_rank', 'vendor_price', 'status_flag',
    ]
    cols = [c for c in export_cols if c in df.columns]
    df[cols].to_csv(OUTPUT_FILE, index=False)
    df.to_json(os.path.join(OUTPUT_DIR, "bids_full.json"), orient='records', indent=2, default_handler=str)

    generate_insights(df, OUTPUT_DIR)

    print(f"\nAll done — {len(df)} records exported")
    print(f"  {OUTPUT_FILE}")
    print(f"  {OUTPUT_DIR}/bids_full.json")
    print(f"  {OUTPUT_DIR}/insights.json")


def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


if __name__ == "__main__":
    main()
