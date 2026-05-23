import re


def get_evaluation_details(enriched_bids):
    records = []

    for i, bid in enumerate(enriched_bids):
        fin_vendors = bid.get('vendors_financial', [])
        tech_vendors = bid.get('vendors_technical', [])

        tech_map = {normalize(v['vendor_name']): v['status'] for v in tech_vendors}

        base = {
            'bid_id': bid.get('bid_id', 'N/A'),
            'category': bid.get('category', 'N/A'),
            'buyer': bid.get('buyer', 'N/A'),
            'quantity': bid.get('quantity', 'N/A'),
            'bid_value': bid.get('bid_value', 'N/A'),
            'award_date': bid.get('award_date', 'N/A'),
            'winner_name': bid.get('winner_name', 'N/A'),
            'winner_price': bid.get('winner_price', 'N/A'),
            'num_bidders': bid.get('num_bidders', 'N/A'),
        }

        for v in fin_vendors:
            tech_status = tech_map.get(normalize(v['vendor_name']), "N/A")
            if tech_status == "N/A":
                tech_status = fuzzy_match(v['vendor_name'], tech_vendors)

            records.append({
                **base,
                'vendor_name': v['vendor_name'],
                'vendor_rank': v['vendor_rank'],
                'vendor_price': v['vendor_price'],
                'status_flag': get_flag(v['vendor_rank'], tech_status),
            })

        fin_names = {normalize(v['vendor_name']) for v in fin_vendors}
        for tv in tech_vendors:
            if 'disqualified' in tv['status'].lower() and normalize(tv['vendor_name']) not in fin_names:
                records.append({
                    **base,
                    'vendor_name': tv['vendor_name'],
                    'vendor_rank': 'Disqualified',
                    'vendor_price': 'N/A',
                    'status_flag': 'disqualified',
                })

        if not fin_vendors and not tech_vendors:
            records.append({**base, 'vendor_name': 'N/A', 'vendor_rank': 'N/A',
                           'vendor_price': 'N/A', 'status_flag': 'no_data'})

    print(f"{len(records)} vendor records built")
    return records


def normalize(name):
    name = name.upper()
    name = re.sub(r'\(MSE.*?\)|\(MII.*?\)|UNDER PMA.*$', '', name)
    name = re.sub(r'[^A-Z0-9\s]', '', name)
    return re.sub(r'\s+', ' ', name).strip()


def fuzzy_match(name, tech_vendors):
    words = set(normalize(name).split())
    best, best_score = "N/A", 0

    for tv in tech_vendors:
        tv_words = set(normalize(tv['vendor_name']).split())
        if not words or not tv_words:
            continue
        score = len(words & tv_words) / len(words | tv_words)
        if score > best_score and score > 0.5:
            best, best_score = tv['status'], score

    return best


def get_flag(rank, tech_status):
    if 'disqualified' in tech_status.lower():
        return 'disqualified'
    if rank == 'L1':
        return 'winner'
    if rank in ('L2', 'L3', 'L4', 'L5'):
        return 'participated'
    if 'qualified' in tech_status.lower():
        return 'qualified'
    return 'participated'


if __name__ == "__main__":
    test_data = [{
        'bid_id': 'GEM/2026/B/7497804',
        'category': 'Supply of Superstructure',
        'buyer': 'Ministry of Defence, Department of Military Affairs',
        'quantity': '6',
        'bid_value': '1315000.00',
        'award_date': '22-05-2026 21:00:00',
        'winner_name': 'M/S SHREE DURGA ENTERPRISE',
        'winner_price': '1315000.00',
        'num_bidders': 6,
        'vendors_financial': [
            {'vendor_name': 'M/S SHREE DURGA ENTERPRISE', 'vendor_price': '1315000.00', 'vendor_rank': 'L1'},
            {'vendor_name': 'M/S RAJ ASSOCIATE', 'vendor_price': '1780000.00', 'vendor_rank': 'L2'},
            {'vendor_name': 'SHEKHAWAT INDUSTRIES', 'vendor_price': '1825000.00', 'vendor_rank': 'L3'},
        ],
        'vendors_technical': [
            {'vendor_name': 'AGGARWAL INFRATECH & ENGINEERS', 'status': 'Disqualified'},
            {'vendor_name': 'M/S RAJ ASSOCIATE', 'status': 'Qualified'},
            {'vendor_name': 'M/S SHREE DURGA ENTERPRISE', 'status': 'Qualified'},
            {'vendor_name': 'SHEKHAWAT INDUSTRIES', 'status': 'Qualified'},
            {'vendor_name': 'SHREE SHYAM ENTERPRISES', 'status': 'Disqualified'},
            {'vendor_name': 'VIJAY INDUSTRIES', 'status': 'Disqualified'},
        ],
    }]

    records = get_evaluation_details(test_data)
    print(f"\nRecords: {len(records)}")
    for r in records:
        print(f"  {r['vendor_name'][:30]:30} | {r['vendor_rank']:12} | {r['vendor_price']:15} | {r['status_flag']}")
