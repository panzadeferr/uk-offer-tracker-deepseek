"""
Final MegaList Scraper - Complete Integration
Combines MegaList scraping with existing manual offers and cleanup
"""

import json
import re
import time
import requests
from datetime import datetime
from typing import List, Dict, Set

# ============================================
# CORE PARSING FUNCTIONS (from test)
# ============================================

def strip_markdown(text: str) -> str:
    """Remove markdown formatting from a text string.
    Fixes store/item fields that contain raw **bold**, [links](url)
    and | pipe-separator artifacts from Reddit table parsing.
    """
    # Remove bold/italic markers: **text** or *text*
    text = re.sub(r'\*+([^*\n]+?)\*+', r'\1', text)
    # Remove markdown links: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    # Remove anything after a pipe (table column remnant): "Name | Get £25" → "Name"
    text = re.sub(r'\s*\|.*$', '', text, flags=re.DOTALL)
    # Collapse multiple spaces
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def extract_direct_url(text: str) -> str:
    """Extract destination URL, bypassing Reddit redirects."""
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
    for link_text, url in markdown_links:
        if 'out.reddit.com' in url or 'reddit.com/r/' in url:
            continue
        if re.match(r'https?://(?!.*reddit\.com)[\w\-\.]+\.[a-z]{2,}', url):
            return url
    
    raw_urls = re.findall(r'https?://[^\s\)]+', text)
    for url in raw_urls:
        if 'out.reddit.com' in url or 'reddit.com/r/' in url:
            continue
        if re.match(r'https?://(?!.*reddit\.com)[\w\-\.]+\.[a-z]{2,}', url):
            return url
    
    if markdown_links:
        return markdown_links[0][1]
    return ""

def parse_markdown_table(text: str) -> List[Dict]:
    """Parse markdown tables."""
    offers = []
    table_pattern = r'\|([^\n]+)\|\s*\n\|[-:]+\|\s*\n((?:\|[^\n]+\|\s*\n?)+)'
    tables = re.findall(table_pattern, text, re.MULTILINE)
    
    for header_row, table_body in tables:
        rows = table_body.strip().split('\n')
        for row in rows:
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if len(cells) < 2:
                continue
            
            # FIX: Strip markdown bold markers, links and pipe remnants
            # e.g. "**Tesco Bank**  | Get" → "Tesco Bank"
            offer_name = strip_markdown(cells[0])

            # Skip rows where offer_name looks like a prose sentence
            # (more than 6 words with no capitalised proper noun pattern)
            if len(offer_name.split()) > 6:
                continue

            reward = ""
            for cell in cells:
                amounts = re.findall(r'£(\d+(?:\.\d{2})?)', cell)
                if amounts:
                    # Skip unrealistic totals (megathread intro combined figures)
                    try:
                        if float(amounts[0]) <= 500:
                            reward = f"£{amounts[0]}"
                            break
                    except ValueError:
                        pass
            
            url = ""
            for cell in cells:
                found_url = extract_direct_url(cell)
                if found_url:
                    url = found_url
                    break
            
            requirements = cells[-1] if len(cells) > 2 else cells[1] if len(cells) == 2 else ""
            
            if offer_name and reward:
                offers.append({
                    "store": offer_name[:40],
                    "item": offer_name[:80],
                    "deal_price": reward,
                    "link": url,
                    "requirements": requirements,
                    "type": "scraped_megalist",
                    "source": "MegaList",
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
    
    return offers

def parse_list_items(text: str) -> List[Dict]:
    """Parse numbered/bulleted lists."""
    offers = []
    numbered_pattern = r'^\d+[\.\)]\s+(.+?)(?=\n\d+[\.\)]|\n\n|$)'
    numbered_items = re.findall(numbered_pattern, text, re.MULTILINE | re.DOTALL)
    
    bullet_pattern = r'^[•\-\*]\s+(.+?)(?=\n[•\-\*]|\n\n|$)'
    bullet_items = re.findall(bullet_pattern, text, re.MULTILINE | re.DOTALL)
    
    all_items = numbered_items + bullet_items
    
    for item_text in all_items:
        name_match = re.match(r'^([^£\-]+?)(?=\s*[£\-]|$)', item_text)
        raw_name = name_match.group(1).strip() if name_match else item_text[:50].strip()
        # FIX: Strip **bold**, [links](url) and pipe separators
        offer_name = strip_markdown(raw_name)
        
        reward = ""
        amounts = re.findall(r'£(\d+(?:\.\d{2})?)', item_text)
        if amounts:
            valid_amounts = []
            for amount in amounts:
                try:
                    amount_float = float(amount)
                    if 5 <= amount_float <= 1000:
                        valid_amounts.append(amount_float)
                except ValueError:
                    continue
            if valid_amounts:
                reward = f"£{valid_amounts[0]}"
        
        url = extract_direct_url(item_text)
        requirements = item_text
        
        if offer_name and reward:
            offers.append({
                "store": offer_name[:40],
                "item": offer_name[:80],
                "deal_price": reward,
                "link": url,
                "requirements": requirements,
                "type": "scraped_megalist",
                "source": "MegaList",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return offers

def generate_ai_guide(offer_name: str, reward: str, requirements: str) -> str:
    """Generate natural 3-step guide."""
    req_lower = requirements.lower()
    name_lower = offer_name.lower()
    
    # Step 1
    sign_up_action = "Sign up"
    if "switch" in req_lower or "switch" in name_lower:
        sign_up_action = "Switch account"
    elif "open" in req_lower or "open account" in req_lower:
        sign_up_action = "Open account"
    elif "deposit" in req_lower:
        sign_up_action = "Deposit funds"
    elif "invest" in req_lower:
        sign_up_action = "Invest"
    
    # Step 2
    action_step = "Complete the required steps"
    if "deposit" in req_lower:
        deposit_match = re.search(r'deposit\s+£?(\d+(?:,\d{3})*(?:\.\d{2})?)', req_lower)
        if deposit_match:
            action_step = f"Deposit £{deposit_match.group(1)}"
    elif "spend" in req_lower:
        spend_match = re.search(r'spend\s+£?(\d+(?:,\d{3})*(?:\.\d{2})?)', req_lower)
        if spend_match:
            action_step = f"Spend £{spend_match.group(1)}"
    elif "switch" in req_lower:
        action_step = "Complete the Current Account Switch Service (CASS)"
    elif "refer" in req_lower:
        action_step = "Refer friends (check specific requirements)"
    
    # Step 3
    reward_timing = "Receive your reward"
    timeframes = {
        "30 days": r'30\s+days|within\s+30\s+days',
        "60 days": r'60\s+days|within\s+60\s+days',
        "90 days": r'90\s+days|3\s+months',
        "immediate": r'immediate|instantly|right away',
        "few days": r'few\s+days|several\s+days',
        "7 days": r'7\s+days|within\s+a\s+week'
    }
    for timeframe, pattern in timeframes.items():
        if re.search(pattern, req_lower):
            reward_timing = f"Receive {reward} within {timeframe}"
            break
    
    return f"""1. **{sign_up_action}** - Create an account using the provided link
2. **{action_step}** - Follow the specific requirements to qualify
3. **{reward_timing}** - The bonus will be paid once all conditions are met"""

def scrape_reddit_post(url: str, visited_urls: Set[str] = None) -> List[Dict]:
    """Scrape Reddit post recursively."""
    if visited_urls is None:
        visited_urls = set()
    
    if url in visited_urls:
        return []
    
    visited_urls.add(url)
    offers = []
    
    print(f"📄 Scraping: {url}")
    
    try:
        headers = {"User-Agent": "MoneyHuntersUK/1.0"}
        response = requests.get(url + ".json", headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"   ⚠️ Failed: {response.status_code}")
            return offers
        
        data = response.json()
        post_body = data[0]['data']['children'][0]['data'].get('selftext', '')
        
        # Try tables first
        table_offers = parse_markdown_table(post_body)
        offers.extend(table_offers)
        
        # Fallback to lists
        if not table_offers:
            list_offers = parse_list_items(post_body)
            offers.extend(list_offers)
        
        print(f"   ✅ Found {len(offers)} offers")
        
        # Look for sub-list links
        sublist_links = re.findall(r'\[([^\]]+)\]\((https://www\.reddit\.com/[^)]+)\)', post_body)
        for link_text, link_url in sublist_links:
            guide_keywords = ['list', 'guide', 'offers', 'megathread', 'casino', 'bank', 'switch']
            if any(keyword in link_text.lower() for keyword in guide_keywords):
                if link_url.startswith('https://www.reddit.com/'):
                    print(f"   🔗 Following: {link_text}")
                    time.sleep(1)
                    sub_offers = scrape_reddit_post(link_url, visited_urls)
                    offers.extend(sub_offers)
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return offers

# ============================================
# DATA INTEGRATION FUNCTIONS
# ============================================

def load_existing_deals() -> List[Dict]:
    """Load existing deals from all_deals.json."""
    try:
        with open("all_deals.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            return existing_data.get("deals", [])
    except:
        return []

def categorize_deals(deals: List[Dict]) -> tuple:
    """Categorize deals into manual, supermarket, and other."""
    manual_offers = []
    supermarket_deals = []
    other_deals = []
    
    for deal in deals:
        if deal.get('type') in ['bank_switch', 'referral', 'invest', 'cashback', 
                               'business', 'utilities', 'freebies', 'transfer', 
                               'credit', 'travel', 'pension']:
            manual_offers.append(deal)
        elif deal.get('category') == 'supermarket' or deal.get('type') == 'supermarket':
            supermarket_deals.append(deal)
        else:
            other_deals.append(deal)
    
    return manual_offers, supermarket_deals, other_deals

def cleanup_ghost_offers(megalist_offers: List[Dict], existing_deals: List[Dict]) -> List[Dict]:
    """Remove ghost offers (old Reddit scraped offers not in MegaList)."""
    megalist_keys = set()
    for offer in megalist_offers:
        key = f"{offer['store'].lower()}_{offer['deal_price']}"
        megalist_keys.add(key)
    
    cleaned_deals = []
    
    for deal in existing_deals:
        # Always keep manual offers
        if deal.get('type') in ['bank_switch', 'referral', 'invest', 'cashback', 
                               'business', 'utilities', 'freebies', 'transfer', 
                               'credit', 'travel', 'pension']:
            cleaned_deals.append(deal)
            continue
        
        # Always keep supermarket deals
        if deal.get('category') == 'supermarket' or deal.get('type') == 'supermarket':
            cleaned_deals.append(deal)
            continue
        
        # For scraped Reddit offers, check if they're in MegaList
        if deal.get('source') == 'r/beermoneyuk' or deal.get('type') == 'scraped_reddit':
            deal_key = f"{deal['store'].lower()}_{deal['deal_price']}"
            if deal_key in megalist_keys:
                cleaned_deals.append(deal)
            else:
                print(f"   🗑️ Removing ghost offer: {deal['store']} - {deal['deal_price']}")
        else:
            # Keep other scraped offers
            cleaned_deals.append(deal)
    
    return cleaned_deals

def scrape_megalist() -> List[Dict]:
    """Main function to scrape the MegaList and generate AI guides."""
    print("=" * 50)
    print("🤖 MEGALIST SCRAPER STARTING")
    print("=" * 50)
    
    megalist_url = "https://www.reddit.com/r/beermoneyuk/comments/1rywry0/the_beermoney_megalist_march_2026_the_big_list_of/"
    
    all_offers = scrape_reddit_post(megalist_url)
    
    print("\n🤖 GENERATING AI STEP-BY-STEP GUIDES")
    for i, offer in enumerate(all_offers):
        guide = generate_ai_guide(
            offer['store'],
            offer['deal_price'],
            offer.get('requirements', '')
        )
        offer['step_by_step_guide'] = guide
        offer['steps'] = ["Follow the step-by-step guide below"]
        
        print(f"   [{i+1}/{len(all_offers)}] {offer['store']} - {offer['deal_price']} ✓ Guide generated")
    
    print(f"\n✅ Total MegaList offers: {len(all_offers)}")
    return all_offers

def run_complete_scraper():
    """Run the complete enhanced scraper with MegaList integration."""
    print("🛒 ENHANCED MONEY HUNTERS SCRAPER")
    print("=" * 50)
    
    # 1. Load existing deals
    existing_deals = load_existing_deals()
    print(f"📦 Loaded {len(existing_deals)} existing deals")
    
    # 2. Categorize existing deals
    manual_offers, supermarket_deals, other_deals = categorize_deals(existing_deals)
    
    print(f"\n📊 Breakdown of existing data:")
    print(f"   - Manual offers: {len(manual_offers)}")
    print(f"   - Supermarket deals: {len(supermarket_deals)}")
    print(f"   - Other scraped offers: {len(other_deals)}")
    
    # 3. Scrape MegaList
    print("\n📡 SCRAPING MEGALIST")
    megalist_offers = scrape_megalist()
    
    # 4. Combine all offers
    all_deals = []
    all_deals.extend(manual_offers)
    all_deals.extend(supermarket_deals)
    all_deals.extend(megalist_offers)
    
    # 5. Clean up ghost offers
    print("\n🧹 CLEANING UP GHOST OFFERS")
    cleaned_deals = cleanup_ghost_offers(megalist_offers, all_deals)
    
    # 6. Add missing fields
    for deal in cleaned_deals:
        if 'category' not in deal:
            store_lower = deal.get('store', '').lower()
            if any(keyword in store_lower for keyword in ['tesco', 'sainsbury', 'asda', 'iceland', 'morrisons', 'waitrose', 'aldi', 'lidl']):
                deal['category'] = 'supermarket'
            elif any(keyword in store_lower for keyword in ['bank', 'lloyds', 'chase', 'monzo', 'revolut', 'halifax', 'natwest']):
                deal['category'] = 'bank_switch'
            elif any(keyword in store_lower for keyword in ['invest', 'share', 'freetrade', 'robinhood', 'plum', 'webull']):
                deal['category'] = 'investment'
            elif any(keyword in store_lower for keyword in ['cashback', 'quidco', 'rakuten', 'airtime', 'cheddar']):
                deal['category'] = 'cashback'
            else:
                deal['category'] = 'other'
        
        deal['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 7. Save to JSON
    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_deals": len(cleaned_deals),
        "manual_count": len(manual_offers),
        "supermarket_count": len(supermarket_deals),
        "megalist_count": len(megalist_offers),
        "cleaned_count": len(cleaned_deals) - len(manual_offers) - len(supermarket_deals),
        "sources": ["Manual", "Supermarket", "MegaList"],
        "deals": cleaned_deals
    }
    
    with open("all_deals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # 8. Write log
    log = [
        f"Enhanced scraper run: {datetime.now()}",
        f"Manual offers preserved: {len(manual_offers)}",
        f"Supermarket deals preserved: {len(supermarket_deals)}",
        f"MegaList offers found: {len(megalist_offers)}",
        f"Total offers saved: {len(cleaned_deals)}",
        f"Ghost offers removed: {len(all_deals) - len(cleaned_deals)}",
        f"AI guides generated: {len(megalist_offers)}"
    ]
    
    with open("scrape_log.txt", "w") as f:
        f.write("\n".join(log))
    
    print("-" * 40)
    print(f"✅ ENHANCED SCRAPER COMPLETE")
    print(f"   - Manual offers: {len(manual_offers)}")
    print(f"   - Supermarket deals: {len(supermarket_deals)}")
    print(f"   - MegaList offers: {len(megalist_offers)}")
    print(f"   - Ghost offers removed: {len(all_deals) - len(cleaned_deals)}")
    print(f"   - Total saved: {len(cleaned_deals)}")
    print(f"   - AI guides generated: {len(megalist_offers)}")
    print(f"💾 Saved to all_deals.json")
    print(f"📝 Log written to scrape_log.txt")
    
    return output


# ============================================
# RUN THE SCRAPER
# ============================================

if __name__ == "__main__":
    run_complete_scraper()
