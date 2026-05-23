import pandas as pd
import json
import os


def generate_insights(df, output_dir="output"):
    if df.empty:
        return {}

    insights = {}

    insights['total_bids'] = int(df['bid_id'].nunique())
    insights['total_vendor_records'] = len(df)

    insights['competition'] = competition_analysis(df)
    insights['price_analysis'] = price_analysis(df)
    insights['repeat_winners'] = repeat_winner_analysis(df)
    insights['disqualification'] = disqualification_analysis(df)

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "insights.json")
    with open(path, 'w') as f:
        json.dump(insights, f, indent=2, default=str)
    print_summary(insights)
    return insights


def competition_analysis(df):
    bid_bidders = df.groupby('bid_id')['num_bidders'].first()
    bid_bidders = pd.to_numeric(bid_bidders, errors='coerce').dropna()

    total = len(bid_bidders)
    if total == 0:
        return {}

    more_than_3 = (bid_bidders > 3).sum()

    return {
        'avg_bidders_per_bid': round(bid_bidders.mean(), 1),
        'max_bidders': int(bid_bidders.max()),
        'min_bidders': int(bid_bidders.min()),
        'bids_with_more_than_3_bidders': int(more_than_3),
        'pct_bids_with_more_than_3': round(more_than_3 / total * 100, 1),
    }


def price_analysis(df):
    winners = df[df['status_flag'] == 'winner'].copy()
    l2 = df[df['vendor_rank'] == 'L2'].copy()

    result = {}

    if 'winner_price_numeric' in winners.columns and not winners.empty:
        prices = winners['winner_price_numeric'].dropna()
        result['avg_winning_price'] = round(prices.mean(), 2)
        result['max_winning_price'] = round(prices.max(), 2)
        result['min_winning_price'] = round(prices.min(), 2)

    if not winners.empty and not l2.empty and 'vendor_price_numeric' in l2.columns:
        gaps = []
        for bid_id in winners['bid_id'].unique():
            w = winners[winners['bid_id'] == bid_id]['winner_price_numeric'].values
            l = l2[l2['bid_id'] == bid_id]['vendor_price_numeric'].values
            if len(w) > 0 and len(l) > 0 and w[0] > 0:
                gap_pct = round((l[0] - w[0]) / w[0] * 100, 1)
                gaps.append(gap_pct)

        if gaps:
            result['avg_l1_l2_gap_pct'] = round(sum(gaps) / len(gaps), 1)
            result['max_l1_l2_gap_pct'] = round(max(gaps), 1)
            result['min_l1_l2_gap_pct'] = round(min(gaps), 1)

    return result


def repeat_winner_analysis(df):
    winners = df[df['status_flag'] == 'winner']
    if winners.empty:
        return {}

    win_counts = winners.groupby('vendor_name')['bid_id'].nunique().sort_values(ascending=False)
    repeats = win_counts[win_counts > 1]

    return {
        'total_unique_winners': int(len(win_counts)),
        'repeat_winners': {name: int(count) for name, count in repeats.items()},
        'top_5_winners': {name: int(count) for name, count in win_counts.head(5).items()},
    }


def disqualification_analysis(df):
    disq = df[df['status_flag'] == 'disqualified']
    total_vendors = len(df[df['vendor_name'].notna()])

    return {
        'total_disqualified': int(len(disq)),
        'disqualification_rate_pct': round(len(disq) / total_vendors * 100, 1) if total_vendors > 0 else 0,
        'top_disqualified_vendors': disq['vendor_name'].value_counts().head(5).to_dict(),
    }


def print_summary(insights):
    print("\n--- Insights Summary ---")
    print(f"  Total bids analyzed: {insights['total_bids']}")
    print(f"  Total vendor records: {insights['total_vendor_records']}")

    comp = insights.get('competition', {})
    if comp:
        print(f"  Avg bidders per bid: {comp.get('avg_bidders_per_bid')}")
        print(f"  Bids with >3 bidders: {comp.get('pct_bids_with_more_than_3')}%")

    price = insights.get('price_analysis', {})
    if price.get('avg_l1_l2_gap_pct') is not None:
        print(f"  Avg L1-L2 price gap: {price['avg_l1_l2_gap_pct']}%")

    rep = insights.get('repeat_winners', {})
    if rep.get('repeat_winners'):
        print(f"  Repeat winners: {len(rep['repeat_winners'])}")

    disq = insights.get('disqualification', {})
    if disq:
        print(f"  Disqualification rate: {disq.get('disqualification_rate_pct')}%")


if __name__ == "__main__":
    test_df = pd.DataFrame([
        {'bid_id': 'B1', 'vendor_name': 'ACME', 'vendor_rank': 'L1', 'vendor_price_numeric': 100000, 'winner_price_numeric': 100000, 'status_flag': 'winner', 'num_bidders': 4},
        {'bid_id': 'B1', 'vendor_name': 'XYZ', 'vendor_rank': 'L2', 'vendor_price_numeric': 120000, 'winner_price_numeric': 100000, 'status_flag': 'participated', 'num_bidders': 4},
        {'bid_id': 'B1', 'vendor_name': 'FAIL Corp', 'vendor_rank': 'Disqualified', 'vendor_price_numeric': None, 'winner_price_numeric': 100000, 'status_flag': 'disqualified', 'num_bidders': 4},
        {'bid_id': 'B2', 'vendor_name': 'ACME', 'vendor_rank': 'L1', 'vendor_price_numeric': 200000, 'winner_price_numeric': 200000, 'status_flag': 'winner', 'num_bidders': 2},
    ])
    generate_insights(test_df)
