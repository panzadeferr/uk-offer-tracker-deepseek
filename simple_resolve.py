#!/usr/bin/env python3
"""
Simple script to resolve the merge conflict in all_deals.json
by manually creating a merged version that protects manual referrals.
"""

import json
import re
from datetime import datetime

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_manual_deal(deal):
    """Check if deal is a manual referral."""
    deal_type = deal.get('type', '').lower()
    source = deal.get('source', '').lower()
    
    # Manual deals have specific types
    manual_types = {'manual', 'bank_switch', 'invest', 'cashback', 'business', 
                   'freebies', 'supermarket', 'travel', 'utilities', 'transfer', 
                   'other', 'credit', 'pension', 'referral'}
    
    if deal_type in manual_types:
        return True
    
    # Check if it's from scraped sources
    if 'scraped' in deal_type or 'scraped' in source:
        return False
    
    # Check for manual deal patterns
    if deal.get('steps') and len(deal.get('steps', [])) > 0:
        return True
    
    return False

def is_scraped_deal(deal):
    """Check if deal is scraped from megalist."""
    deal_type = deal.get('type', '').lower()
    source = deal.get('source', '').lower()
    
    return 'scraped' in deal_type or 'megalist' in source or 'scrimpr' in source

def normalize_store_name(store):
    """Normalize store name for comparison."""
    if not store:
        return ""
    store = re.sub(r'[^a-zA-Z0-9\s]', '', store)
    store = re.sub(r'\s+', ' ', store).strip().lower()
    return store

def find_similar_deal(existing_deals, new_deal):
    """Check if a similar deal already exists."""
    new_store = normalize_store_name(new_deal.get('store', ''))
    new_item = new_deal.get('item', '').lower()
    
    for existing in existing_deals:
        existing_store = normalize_store_name(existing.get('store', ''))
        existing_item = existing.get('item', '').lower()
        
        # Check for similar store names
        if new_store and existing_store:
            if new_store in existing_store or existing_store in new_store:
                # Check for similar items
                if new_item and existing_item:
                    if new_item in existing_item or existing_item in new_item:
                        return True
    return False

def main():
    print("Resolving merge conflict in all_deals.json")
    print("=" * 60)
    
    # Read the conflicted file
    with open('all_deals.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by conflict markers
    parts = content.split('<<<<<<< HEAD')
    if len(parts) < 2:
        print("No conflict markers found")
        return
    
    # Get the HEAD section (before =======)
    head_part = parts[1].split('=======')[0]
    
    # Get the local section (after =======)
    local_part = parts[1].split('=======')[1].split('>>>>>>>')[0]
    
    # Parse the JSON from HEAD (remote) version
    # We need to reconstruct the full JSON
    head_json_str = '{' + head_part
    try:
        head_json = json.loads(head_json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing HEAD JSON: {e}")
        # Try to fix common issues
        head_json_str = head_json_str.replace('\n', ' ').replace('\r', '')
        head_json = json.loads(head_json_str)
    
    # Parse the JSON from local version
    local_json_str = '{' + local_part
    try:
        local_json = json.loads(local_json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing local JSON: {e}")
        # Try to fix common issues
        local_json_str = local_json_str.replace('\n', ' ').replace('\r', '')
        local_json = json.loads(local_json_str)
    
    print(f"HEAD version has {len(head_json.get('deals', []))} deals")
    print(f"Local version has {len(local_json.get('deals', []))} deals")
    
    # Start with manual deals from HEAD (protect manual referrals)
    merged_deals = []
    seen_stores = set()
    
    # Add all manual deals from HEAD first
    for deal in head_json.get('deals', []):
        if is_manual_deal(deal):
            store = normalize_store_name(deal.get('store', ''))
            if store not in seen_stores:
                merged_deals.append(deal)
                seen_stores.add(store)
    
    print(f"Added {len(merged_deals)} manual deals from HEAD")
    
    # Add manual deals from local version (if not duplicates)
    local_manual_added = 0
    for deal in local_json.get('deals', []):
        if is_manual_deal(deal):
            store = normalize_store_name(deal.get('store', ''))
            if store not in seen_stores and not find_similar_deal(merged_deals, deal):
                merged_deals.append(deal)
                seen_stores.add(store)
                local_manual_added += 1
    
    print(f"Added {local_manual_added} manual deals from local")
    
    # Add scraped deals from local version (megalist integration)
    scraped_added = 0
    for deal in local_json.get('deals', []):
        if is_scraped_deal(deal):
            store = normalize_store_name(deal.get('store', ''))
            # Don't add if similar manual deal exists
            if not find_similar_deal(merged_deals, deal):
                merged_deals.append(deal)
                scraped_added += 1
    
    print(f"Added {scraped_added} scraped deals from megalist")
    
    # Create merged metadata
    manual_count = sum(1 for d in merged_deals if is_manual_deal(d))
    supermarket_count = sum(1 for d in merged_deals if 'supermarket' in d.get('category', '').lower())
    megalist_count = sum(1 for d in merged_deals if is_scraped_deal(d))
    
    merged_json = {
        "last_updated": now_str(),
        "total_deals": len(merged_deals),
        "manual_count": manual_count,
        "supermarket_count": supermarket_count,
        "megalist_count": megalist_count,
        "cleaned_count": megalist_count,
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
    
    # Write merged file
    with open('all_deals.json', 'w', encoding='utf-8') as f:
        json.dump(merged_json, f, indent=2, ensure_ascii=False)
    
    print(f"\nMerge completed successfully!")
    print(f"Total merged deals: {len(merged_deals)}")
    print(f"Manual referrals: {manual_count}")
    print(f"Supermarket deals: {supermarket_count}")
    print(f"Megalist scraped deals: {megalist_count}")
    print(f"\nOutput saved to: all_deals.json")
    
    # Show sample
    print("\nSample of merged deals (first 10):")
    for i, deal in enumerate(merged_deals[:10]):
        source = "Manual" if is_manual_deal(deal) else "Scraped"
        print(f"{i+1}. {deal.get('store', 'Unknown')} - {deal.get('deal_price', 'N/A')} ({source})")

if __name__ == "__main__":
    main()