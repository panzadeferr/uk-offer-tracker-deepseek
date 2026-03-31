#!/usr/bin/env python3
"""
Resolve merge conflict in all_deals.json with de-duplication logic.
Protects manual referrals while adding scraped megalist deals.
"""

import json
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Tuple

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def normalize_store_name(store: str) -> str:
    """Normalize store name for comparison."""
    if not store:
        return ""
    # Remove special characters, extra spaces, convert to lowercase
    store = re.sub(r'[^a-zA-Z0-9\s]', '', store)
    store = re.sub(r'\s+', ' ', store).strip().lower()
    return store

def normalize_item_name(item: str) -> str:
    """Normalize item name for comparison."""
    if not item:
        return ""
    # Remove special characters, extra spaces, convert to lowercase
    item = re.sub(r'[^a-zA-Z0-9\s]', '', item)
    item = re.sub(r'\s+', ' ', item).strip().lower()
    return item

def extract_numeric_value(price_str: str) -> float:
    """Extract numeric value from price string."""
    if not price_str:
        return 0.0
    # Remove currency symbols, commas, and non-numeric characters
    price_str = str(price_str)
    match = re.search(r'[\d,.]+', price_str)
    if match:
        try:
            value = float(match.group().replace(',', ''))
            return value
        except ValueError:
            pass
    return 0.0

def generate_deal_id(store: str, item: str, deal_price: str) -> str:
    """Generate unique ID for a deal."""
    seed = f"{store}|{item}|{deal_price}".strip().lower()
    # Create a base slug
    base = re.sub(r'[^a-z0-9]+', '-', store.lower())[:40]
    # Add hash for uniqueness
    digest = hashlib.md5(seed.encode('utf-8')).hexdigest()[:8]
    return f"{base}-{digest}"

def is_manual_deal(deal: Dict) -> bool:
    """Check if deal is a manual referral (not scraped)."""
    deal_type = deal.get('type', '').lower()
    source = deal.get('source', '').lower()
    
    # Manual deals have specific types or no type
    manual_types = {'manual', 'bank_switch', 'invest', 'cashback', 'business', 'freebies', 'supermarket', 'travel', 'utilities', 'transfer', 'other'}
    
    if deal_type in manual_types:
        return True
    
    # Check if it's from manual sources
    if 'scraped' in deal_type or 'scraped' in source:
        return False
    
    # Check for manual deal patterns
    if deal.get('steps') and len(deal.get('steps', [])) > 0:
        # Manual deals have detailed steps
        return True
    
    return False

def is_scraped_deal(deal: Dict) -> bool:
    """Check if deal is scraped from megalist."""
    deal_type = deal.get('type', '').lower()
    source = deal.get('source', '').lower()
    
    return 'scraped' in deal_type or 'megalist' in source or 'scrimpr' in source

def find_similar_deals(existing_deal: Dict, new_deal: Dict) -> bool:
    """Check if two deals are similar (potential duplicates)."""
    # Normalize store names
    store1 = normalize_store_name(existing_deal.get('store', ''))
    store2 = normalize_store_name(new_deal.get('store', ''))
    
    # Normalize item names
    item1 = normalize_item_name(existing_deal.get('item', ''))
    item2 = normalize_item_name(new_deal.get('item', ''))
    
    # Extract numeric values
    price1 = extract_numeric_value(existing_deal.get('deal_price', ''))
    price2 = extract_numeric_value(new_deal.get('deal_price', ''))
    
    # Check for similar store names
    store_similarity = False
    if store1 and store2:
        # Check if one store name contains the other
        if store1 in store2 or store2 in store1:
            store_similarity = True
        # Check for common store patterns
        common_stores = ['tesco', 'asda', 'sainsbury', 'waitrose', 'morrisons', 'iceland', 'aldi', 'lidl']
        for common in common_stores:
            if common in store1 and common in store2:
                store_similarity = True
                break
    
    # Check for similar items
    item_similarity = False
    if item1 and item2:
        # Check if one item name contains the other
        if item1 in item2 or item2 in item1:
            item_similarity = True
    
    # Check for similar prices (within 10%)
    price_similarity = False
    if price1 > 0 and price2 > 0:
        ratio = min(price1, price2) / max(price1, price2)
        if ratio > 0.9:  # Within 10%
            price_similarity = True
    
    # Consider deals similar if store is similar AND (item is similar OR price is similar)
    if store_similarity and (item_similarity or price_similarity):
        return True
    
    return False

def merge_deals(head_deals: List[Dict], local_deals: List[Dict]) -> Tuple[List[Dict], Dict]:
    """
    Merge deals from HEAD and local versions.
    Returns merged deals and statistics.
    """
    merged = []
    seen_ids = set()
    stats = {
        'total_merged': 0,
        'manual_kept': 0,
        'scraped_added': 0,
        'duplicates_removed': 0,
        'manual_duplicates_protected': 0
    }
    
    # First, add all manual deals from HEAD (protect manual referrals)
    for deal in head_deals:
        if is_manual_deal(deal):
            # Generate ID if not present
            if 'id' not in deal:
                deal['id'] = generate_deal_id(
                    deal.get('store', ''),
                    deal.get('item', ''),
                    deal.get('deal_price', '')
                )
            
            if deal['id'] not in seen_ids:
                merged.append(deal)
                seen_ids.add(deal['id'])
                stats['manual_kept'] += 1
                stats['total_merged'] += 1
    
    # Then, add manual deals from local version (if not already present)
    for deal in local_deals:
        if is_manual_deal(deal):
            # Generate ID if not present
            if 'id' not in deal:
                deal['id'] = generate_deal_id(
                    deal.get('store', ''),
                    deal.get('item', ''),
                    deal.get('deal_price', '')
                )
            
            # Check if similar deal already exists
            is_duplicate = False
            for existing in merged:
                if find_similar_deals(existing, deal):
                    is_duplicate = True
                    stats['manual_duplicates_protected'] += 1
                    break
            
            if not is_duplicate and deal['id'] not in seen_ids:
                merged.append(deal)
                seen_ids.add(deal['id'])
                stats['manual_kept'] += 1
                stats['total_merged'] += 1
    
    # Finally, add scraped deals from local version (megalist integration)
    for deal in local_deals:
        if is_scraped_deal(deal):
            # Generate ID if not present
            if 'id' not in deal:
                deal['id'] = generate_deal_id(
                    deal.get('store', ''),
                    deal.get('item', ''),
                    deal.get('deal_price', '')
                )
            
            # Check if similar manual deal already exists
            is_duplicate = False
            for existing in merged:
                if is_manual_deal(existing) and find_similar_deals(existing, deal):
                    # Don't add scraped deal if similar manual deal exists
                    is_duplicate = True
                    stats['duplicates_removed'] += 1
                    break
            
            if not is_duplicate and deal['id'] not in seen_ids:
                merged.append(deal)
                seen_ids.add(deal['id'])
                stats['scraped_added'] += 1
                stats['total_merged'] += 1
    
    return merged, stats

def update_metadata(merged_deals: List[Dict]) -> Dict:
    """Update metadata for merged deals."""
    # Count by type
    manual_count = sum(1 for d in merged_deals if is_manual_deal(d))
    supermarket_count = sum(1 for d in merged_deals if 'supermarket' in d.get('category', '').lower())
    megalist_count = sum(1 for d in merged_deals if is_scraped_deal(d))
    
    # Calculate cleaned count (non-duplicate scraped deals)
    cleaned_count = megalist_count
    
    metadata = {
        "last_updated": now_str(),
        "total_deals": len(merged_deals),
        "manual_count": manual_count,
        "supermarket_count": supermarket_count,
        "megalist_count": megalist_count,
        "cleaned_count": cleaned_count,
        "sources": [
            "Manual",
            "Supermarket",
            "Reddit r/beermoneyuk",
            "Google News",
            "HotUKDeals",
            "MegaList"
        ],
        "stacking_rates": {
            "Tesco": 5.3,
            "Sainsbury's": 4.4,
            "Asda": 4.5,
            "Iceland": 5.0,
            "Morrisons": 4.0,
            "Waitrose": 3.5,
            "Aldi": 2.0,
            "Lidl": 2.0
        },
        "deals": merged_deals
    }
    
    return metadata

def main():
    """Main function to resolve merge conflict."""
    print("=" * 60)
    print("Resolving merge conflict in all_deals.json")
    print("=" * 60)
    
    # Read the conflicted file
    with open('all_deals.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse HEAD and local versions from conflict markers
    head_section = []
    local_section = []
    current_section = None
    
    for line in content.split('\n'):
        if line.startswith('<<<<<<< HEAD'):
            current_section = 'head'
        elif line.startswith('======='):
            current_section = 'local'
        elif line.startswith('>>>>>>>'):
            current_section = None
        elif current_section == 'head':
            head_section.append(line)
        elif current_section == 'local':
            local_section.append(line)
    
    # Parse JSON from sections
    head_json = json.loads('\n'.join(head_section))
    local_json = json.loads('\n'.join(local_section))
    
    print(f"HEAD version: {head_json.get('total_deals', 0)} deals")
    print(f"Local version: {local_json.get('total_deals', 0)} deals")
    
    # Merge deals
    merged_deals, stats = merge_deals(
        head_json.get('deals', []),
        local_json.get('deals', [])
    )
    
    # Update metadata
    merged_json = update_metadata(merged_deals)
    
    # Write merged file
    with open('all_deals.json', 'w', encoding='utf-8') as f:
        json.dump(merged_json, f, indent=2, ensure_ascii=False)
    
    print("\nMerge completed successfully!")
    print(f"Total merged deals: {stats['total_merged']}")
    print(f"Manual referrals kept: {stats['manual_kept']}")
    print(f"Scraped deals added: {stats['scraped_added']}")
    print(f"Duplicates removed: {stats['duplicates_removed']}")
    print(f"Manual duplicates protected: {stats['manual_duplicates_protected']}")
    print(f"\nOutput saved to: all_deals.json")
    
    # Show sample of merged deals
    print("\nSample of merged deals (first 5):")
    for i, deal in enumerate(merged_deals[:5]):
        source = "Manual" if is_manual_deal(deal) else "Scraped"
        print(f"{i+1}. {deal.get('store', 'Unknown')} - {deal.get('deal_price', 'N/A')} ({source})")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()