import pandas as pd
import re


def clean_data(records):
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    df = normalize_text_columns(df)
    df = clean_prices(df)
    df = handle_missing_values(df)
    df = remove_duplicates(df)
    df = flag_anomalies(df)

    return df


def normalize_text_columns(df):
    text_cols = ['vendor_name', 'winner_name', 'category', 'buyer']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].apply(lambda x: re.sub(r'\s+', ' ', x))
    return df


def clean_prices(df):
    junk = ['`', '₹', ',', '(Bid Price)']
    for col in ['vendor_price', 'winner_price', 'bid_value']:
        if col not in df.columns:
            continue
        series = df[col].astype(str)
        for ch in junk:
            series = series.str.replace(ch, '', regex=False)
        df[col] = series.str.strip()
        df[col + '_numeric'] = pd.to_numeric(df[col], errors='coerce')
    return df


def handle_missing_values(df):
    df.replace(['N/A', 'n/a', 'NA', '', 'None', 'null'], pd.NA, inplace=True)

    if 'quantity' in df.columns:
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

    return df


def remove_duplicates(df):
    key_cols = ['bid_id', 'vendor_name', 'vendor_rank']
    existing = [c for c in key_cols if c in df.columns]
    return df.drop_duplicates(subset=existing, keep='first')


def flag_anomalies(df):
    df['anomaly'] = ''

    if 'vendor_price_numeric' in df.columns and 'winner_price_numeric' in df.columns:
        mask = (df['vendor_price_numeric'] < df['winner_price_numeric'] * 0.1) & df['vendor_price_numeric'].notna()
        df.loc[mask, 'anomaly'] += 'suspiciously_low_price;'

    if 'num_bidders' in df.columns:
        single = df['num_bidders'] == 1
        df.loc[single, 'anomaly'] += 'single_bidder;'

    if 'vendor_price_numeric' in df.columns:
        zero_price = df['vendor_price_numeric'] == 0
        df.loc[zero_price, 'anomaly'] += 'zero_price;'

    if 'vendor_price_numeric' in df.columns and 'winner_price_numeric' in df.columns:
        lowest = df.groupby('bid_id')['vendor_price_numeric'].transform('min')
        winner_rows = df[df['status_flag'] == 'winner'].copy()
        winner_rows = winner_rows[winner_rows['winner_price_numeric'] > lowest.loc[winner_rows.index]]
        bad_bids = set(winner_rows['bid_id'])
        if bad_bids:
            df.loc[df['bid_id'].isin(bad_bids), 'anomaly'] += 'winner_not_lowest_price;'

    df['anomaly'] = df['anomaly'].str.rstrip(';')
    return df


