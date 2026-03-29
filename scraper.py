"""
Complete Money Hunters Scraper
- 30+ manual offers (bank switches, referrals, cashback)
- Supermarket deals with stacked prices
- Telegram notifications
"""

import json
import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict

# ============================================
# TELEGRAM SETUP (Optional)
# ============================================

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_to_telegram(deal: Dict) -> bool:
    """Send a deal to Telegram channel"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        import requests
        message = f"""
🛒 *{deal['store']}* - {deal['item']}
💰 Deal Price: {deal['deal_price']}
📊 Stacked Price: *£{deal['stacked_price']:.2f}*
💡 Save with {deal['best_payment_method']}
🔗 {deal['link']}
        """.strip()
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception:
        return False


# ============================================
# STACKING RATES (Per Store)
# ============================================

STACKING_RATES = {
    "Tesco": 5.3,
    "Sainsbury's": 4.4,
    "Asda": 4.5,
    "Iceland": 5.0,
    "Morrisons": 4.0,
    "Waitrose": 3.5,
    "Aldi": 2.0,
    "Lidl": 2.0
}

BEST_PAYMENT = {
    "Tesco": "EverUp (4.9%) + Clubcard",
    "Sainsbury's": "JamDoughnut (4.1%) + Nectar",
    "Asda": "Airtime Rewards (4%) + Asda Rewards",
    "Iceland": "TopCashback (3.5%) + Bonus Card",
    "Morrisons": "Cheddar (3%) + More Card",
    "Waitrose": "JamDoughnut (3.5%) + MyWaitrose",
    "Aldi": "No gift cards, but use cashback credit card",
    "Lidl": "No gift cards, but use cashback credit card"
}


# ============================================
# 30+ MANUAL OFFERS (Bank Switches, Referrals, Cashback)
# ============================================

def get_manual_offers() -> List[Dict]:
    """All your original BeermoneyUK offers"""
    return [
        # BANK SWITCH OFFERS
        {"store": "Lloyds Bank", "item": "Open Account + Switch", "deal_price": "£250", "link": "https://apply.lloydsbank.co.uk/sales-content/cwa/l/onboardpca/index-app.html?from=ob&webDirect=true&redesign=true&token=JpGVwskEUPxoFpO3Mg4RTAUZg6q6Emjz578QtNaABT8=&redesign=true#/refer-friend", "original_price": "£0", "saving_percent": 100, "type": "bank_switch", "code": "", "steps": ["Open account", "Switch using CASS", "Get £250"], "timeFrame": "30 days"},
        {"store": "Chase UK", "item": "Deposit £1,000 → £50", "deal_price": "£50", "link": "https://chase.co.uk/raf", "original_price": "£0", "saving_percent": 100, "type": "bank_switch", "code": "J2SK9W", "steps": ["Copy code J2SK9W", "Open account", "Deposit £1,000 in 30 days"], "timeFrame": "30 days"},
        {"store": "Monzo", "item": "Spend £1 → Get £5-£50", "deal_price": "£5-£50", "link": "https://join.monzo.com/r/", "original_price": "£1", "saving_percent": 90, "type": "referral", "code": "", "steps": ["Sign up", "Spend £1", "Get bonus"], "timeFrame": "Immediate"},
        {"store": "Revolut", "item": "Spend £1 → Get £20", "deal_price": "£20", "link": "https://revolut.com/referral/?referral-code=ludoviv2sq!MAR1-26-AR-H2&geo-redirect", "original_price": "£1", "saving_percent": 95, "type": "referral", "code": "", "steps": ["Sign up", "Spend £1", "Get £20"], "timeFrame": "~1 month"},
        {"store": "First Direct", "item": "Switch Account → £175", "deal_price": "£175", "link": "https://www.firstdirect.com/banking/switch/", "original_price": "£0", "saving_percent": 100, "type": "bank_switch", "code": "", "steps": ["Switch using CASS", "Pay in £1,000", "Get £175"], "timeFrame": "30 days"},
        {"store": "Halifax", "item": "Switch Account → £150", "deal_price": "£150", "link": "https://www.halifax.co.uk/currentaccounts/", "original_price": "£0", "saving_percent": 100, "type": "bank_switch", "code": "", "steps": ["Switch using CASS", "Pay in £1,500", "Get £150"], "timeFrame": "30 days"},
        {"store": "NatWest", "item": "Switch Account → £200", "deal_price": "£200", "link": "https://www.natwest.com/current-accounts/switch/", "original_price": "£0", "saving_percent": 100, "type": "bank_switch", "code": "", "steps": ["Switch using CASS", "2 direct debits", "Get £200"], "timeFrame": "30 days"},
        
        # INVESTMENT OFFERS
        {"store": "Freetrade", "item": "Deposit £1 → Free Share (£10-£100)", "deal_price": "£10-£100", "link": "https://magic.freetrade.io/join/alberto/6f308795", "original_price": "£1", "saving_percent": 90, "type": "invest", "code": "", "steps": ["Deposit £1", "Get free share"], "timeFrame": "Few days"},
        {"store": "Robinhood", "item": "Deposit £1 → Free Share", "deal_price": "£10-£140", "link": "https://join.robinhood.com/albertb-d5dfe0", "original_price": "£1", "saving_percent": 90, "type": "invest", "code": "", "steps": ["Deposit £1", "Get free share"], "timeFrame": "Few days"},
        {"store": "Plum", "item": "Refer 3 Friends → £75", "deal_price": "£75", "link": "https://friends.withplum.com/r/RxK7c2fUNa", "original_price": "£0", "saving_percent": 100, "type": "invest", "code": "", "steps": ["Join Plum", "Refer 3 friends", "Get £75"], "timeFrame": "Expires April 7th"},
        {"store": "Webull", "item": "Deposit £500 → £50 Credit", "deal_price": "£50", "link": "https://www.webull-uk.com/s/zEUukbJam8GjmUx6yq", "original_price": "£500", "saving_percent": 10, "type": "invest", "code": "", "steps": ["Deposit £500", "Keep 60 days", "Get £50"], "timeFrame": "60 days"},
        {"store": "Wealthify", "item": "Invest £1,000 → £50 Bonus", "deal_price": "£50", "link": "https://invest.wealthify.com/refer/81122944", "original_price": "£1,000", "saving_percent": 5, "type": "invest", "code": "", "steps": ["Invest £1,000", "Hold 6 months", "Get £50"], "timeFrame": "6 months"},
        {"store": "Moneybox", "item": "Save & Invest - Great for DDs", "deal_price": "Bonus", "link": "https://go.onelink.me/5M0L?pid=share&c=EN8YW8", "original_price": "£0", "saving_percent": 0, "type": "invest", "code": "", "steps": ["Download Moneybox", "Perfect for direct debits"], "timeFrame": "Ongoing"},
        
        # CASHBACK SITES
        {"store": "TopCashback", "item": "Cashback Site - £10 Bonus", "deal_price": "£10", "link": "https://www.topcashback.co.uk/ref/Panzadeferr/?source_id=4", "original_price": "£0", "saving_percent": 100, "type": "cashback", "code": "", "steps": ["Join TopCashback", "Shop through site"], "timeFrame": "Lifetime"},
        {"store": "Quidco", "item": "Cashback Site - £20 Bonus", "deal_price": "£20", "link": "https://quidco.onelink.me/nKzg/v2f3f7m0", "original_price": "£0", "saving_percent": 100, "type": "cashback", "code": "", "steps": ["Join Quidco", "Earn £5 cashback", "Get £20"], "timeFrame": "After earning £5"},
        {"store": "Rakuten", "item": "Cashback Site - £25 Bonus", "deal_price": "£25", "link": "https://www.rakuten.co.uk/r/ALBERT24541?eeid=28187", "original_price": "£50", "saving_percent": 50, "type": "cashback", "code": "", "steps": ["Join Rakuten", "Spend £50 + VAT", "Get £25"], "timeFrame": "After first purchase"},
        
        # GIFT CARD APPS
        {"store": "Airtime", "item": "Gift Card Cashback - £2 Bonus", "deal_price": "£2", "link": "https://airtimerewards.app.link/6Waa7E1IF1b", "original_price": "£5", "saving_percent": 40, "type": "cashback", "code": "FRJKFXX3", "steps": ["Use code FRJKFXX3", "Spend £5 in 7 days", "Get £2"], "timeFrame": "7 days"},
        {"store": "Cheddar", "item": "Gift Card Cashback - £3 Bonus", "deal_price": "£3", "link": "https://get.cheddar.me/app/FVESBGB", "original_price": "£0", "saving_percent": 100, "type": "cashback", "code": "FVESBGB", "steps": ["Use code FVESBGB", "Earn cashback at retailers"], "timeFrame": "Ongoing"},
        {"store": "Jam Doughnut", "item": "Gift Card Cashback - £3 Bonus", "deal_price": "£3", "link": "https://www.jamdoughnut.com/", "original_price": "£0", "saving_percent": 100, "type": "cashback", "code": "8TGF", "steps": ["Use code 8TGF", "Buy gift cards with cashback"], "timeFrame": "Immediate"},
        {"store": "EverUp", "item": "Gift Card Cashback", "deal_price": "£2", "link": "https://everup.onelink.me/9lgD/3d22pmln", "original_price": "£0", "saving_percent": 100, "type": "cashback", "code": "", "steps": ["Join EverUp", "Link cards", "Earn cashback"], "timeFrame": "Ongoing"},
        
        # BUSINESS ACCOUNTS
        {"store": "Tide", "item": "Business Account - £75 Free", "deal_price": "£75", "link": "https://www.tide.co/", "original_price": "£0", "saving_percent": 100, "type": "business", "code": "3834VA", "steps": ["Sign up for Tide", "Use code 3834VA", "Make first transaction"], "timeFrame": "After first transaction"},
        {"store": "WorldFirst", "item": "Business - Up to £355 Reward", "deal_price": "£355", "link": "https://s.worldfirst.com/2TuviC?default_source=WF-Ts00000OCun2&referral_id=WF-Ts00000OCun2&utm_campaign=COE_MGM_UK_2602&utm_date=app&lang=en_GB", "original_price": "£0", "saving_percent": 100, "type": "business", "code": "", "steps": ["Open WorldFirst", "Make qualifying transactions", "Get up to £355"], "timeFrame": "Varies"},
        
        # UTILITIES
        {"store": "Octopus Energy", "item": "Switch Energy - £50 Credit", "deal_price": "£50", "link": "https://share.octopus.energy/ocean-quoll-258", "original_price": "£0", "saving_percent": 100, "type": "utilities", "code": "", "steps": ["Switch to Octopus", "Use referral link", "Both get £50"], "timeFrame": "After switch"},
        {"store": "Lebara", "item": "Mobile SIM - Referral Bonus", "deal_price": "Discount", "link": "https://aklam.io/hgY3HOvR", "original_price": "£0", "saving_percent": 20, "type": "utilities", "code": "", "steps": ["Sign up for Lebara", "Get great SIM deals"], "timeFrame": "Immediate"},
        
        # FREEBIES
        {"store": "Costa", "item": "Free Cake + Coffee", "deal_price": "Free", "link": "https://www.costa.co.uk/", "original_price": "£5", "saving_percent": 100, "type": "freebies", "code": "", "steps": ["Sign up for Costa Club", "Get free cake & half drink"], "timeFrame": "Immediate"},
        {"store": "Waitrose", "item": "Free Coffee Daily", "deal_price": "Free", "link": "https://www.waitrose.com/", "original_price": "£3", "saving_percent": 100, "type": "freebies", "code": "", "steps": ["Get Waitrose card", "Free tea/coffee daily"], "timeFrame": "Daily"},
        
        # MONEY TRANSFER
        {"store": "Wise", "item": "Free Transfer + Card", "deal_price": "Free", "link": "https://wise.com/invite/ahpc/albertob1508", "original_price": "£5", "saving_percent": 100, "type": "transfer", "code": "", "steps": ["Sign up for Wise", "First transfer free", "Get free card"], "timeFrame": "Immediate"},
        
        # CREDIT CARD
        {"store": "AMEX", "item": "Spend £3,000 → £150+", "deal_price": "£150", "link": "https://americanexpress.com/en-gb/referral/platinum-charge?ref=aLBERBf3Ob&XL=MNMNS", "original_price": "£0", "saving_percent": 100, "type": "credit", "code": "", "steps": ["Apply for AMEX", "Spend £3,000 in 3 months", "Get £150"], "timeFrame": "3 months"},
        
        # TRAVEL
        {"store": "TrainPal", "item": "£3 Off Train Tickets", "deal_price": "£3", "link": "https://t.trainpal.com/wUEPLNq", "original_price": "£0", "saving_percent": 100, "type": "travel", "code": "03ba089c$00", "steps": ["Download TrainPal", "Use code 03ba089c$00", "Save on train tickets"], "timeFrame": "Use within 7 days"},
        
        # OTHER REFERRALS
        {"store": "Zilch", "item": "Sign Up → £5 Free", "deal_price": "£5", "link": "https://zilch.onelink.me/x8EV/zdehyy8s", "original_price": "£0", "saving_percent": 100, "type": "referral", "code": "", "steps": ["Sign up for Zilch", "Get £5 credit instantly"], "timeFrame": "Instant"},
        {"store": "Zopa (Biscuit)", "item": "Open Account → £10 Free", "deal_price": "£10", "link": "https://www.zopa.com/mgma?referralCode=ed204ce1b3dd265fa533", "original_price": "£0", "saving_percent": 100, "type": "referral", "code": "", "steps": ["Open Biscuit account", "Get £10 instantly"], "timeFrame": "Instant"},
        {"store": "PensionBee", "item": "Sign Up → £50 in Pension", "deal_price": "£50", "link": "https://www.pensionbee.com/", "original_price": "£0", "saving_percent": 100, "type": "pension", "code": "", "steps": ["Sign up for PensionBee", "Get £50 in your pension"], "timeFrame": "~1 month"}
    ]


# ============================================
# LIVE WEB SCRAPING FUNCTIONS
# ============================================

def scrape_reddit_beermoneyuk():
    import re
    deals = []
    headers = {
        "User-Agent": "MoneyHuntersUK/1.0 (contact: hello@moneyhunters.co.uk)"
    }
    seen_ids = set()
    endpoints = [
        "https://www.reddit.com/r/beermoneyuk/hot.json?limit=50",
        "https://www.reddit.com/r/beermoneyuk/new.json?limit=50",
        "https://www.reddit.com/r/beermoneyuk/search.json?q=referral+%C2%A3&sort=new&limit=25",
        "https://www.reddit.com/r/beermoneyuk/search.json?q=bank+switch&sort=new&limit=25",
    ]
    for url in endpoints:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                continue
            posts = r.json()["data"]["children"]
            for post in posts:
                d = post["data"]
                pid = d.get("id","")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                title = d.get("title","")
                body = d.get("selftext","")
                score = d.get("score", 0)
                flair = d.get("link_flair_text","") or ""
                # Lower threshold for new posts
                min_score = 1 if "new.json" in url else 3
                if score < min_score:
                    continue
                if "£" not in title and "£" not in body:
                    continue
                amounts = re.findall(
                    r'£(\d+(?:\.\d{2})?)', title+" "+body)
                reward = f"£{amounts[0]}" if amounts else "Bonus"
                code_match = re.search(
                    r'(?:code|referral)[:\s]+([A-Z0-9]{4,15})',
                    title + " " + body, re.IGNORECASE)
                code = code_match.group(1) if code_match else ""
                permalink = "https://reddit.com" + d.get("permalink", "")
                link = d.get("url", permalink)
                deals.append({
                    "store": title[:40],
                    "item": title[:80],
                    "deal_price": reward,
                    "link": link if link.startswith("http") else permalink,
                    "original_price": "£0",
                    "saving_percent": 100,
                    "type": "scraped_reddit",
                    "code": code,
                    "steps": ["Read the Reddit post for full details",
                              "Follow the referral link",
                              "Complete the required steps"],
                    "timeFrame": "Varies",
                    "source": "r/beermoneyuk",
                    "reddit_score": score,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            print(f"Reddit endpoint {url} failed: {e}")
            continue
    print(f"Reddit: found {len(deals)} deals")
    return deals

def scrape_mse_rss():
    """Scrape MoneySavingExpert RSS feed for deals"""
    deals = []
    keywords = ["switch", "bonus", "cashback", "referral",
                "free", "reward", "sign up", "bank", "£"]
    try:
        # Try direct RSS with proper headers first
        url = "https://www.moneysavingexpert.com/rss/deals/"
        headers = {
            "User-Agent": "MoneyHuntersUK/1.0 (contact: hello@moneyhunters.co.uk)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }
        r = requests.get(url, headers=headers, timeout=15)
        print(f"MSE direct RSS status: {r.status_code}")
        
        if r.status_code == 200:
            # Parse XML directly
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
        else:
            # Fallback to feedburner URL which might be more accessible
            print("Trying Feedburner fallback...")
            url = "https://feeds.feedburner.com/MseDeals"
            r = requests.get(url, headers=headers, timeout=15)
            print(f"MSE Feedburner status: {r.status_code}")
            if r.status_code != 200:
                print("MSE RSS unavailable")
                return []
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
        
        for item in items:
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            
            title = title_elem.text if title_elem is not None else ""
            link = link_elem.text if link_elem is not None else ""
            desc = desc_elem.text if desc_elem is not None else ""
            
            combined = (title + " " + desc).lower()
            if not any(kw in combined for kw in keywords):
                continue
            amounts = re.findall(
                r'£(\d+(?:\.\d{2})?)', title + " " + desc)
            reward = f"£{amounts[0]}" if amounts else "Deal"
            deals.append({
                "store": title[:40],
                "item": title[:80],
                "deal_price": reward,
                "link": link,
                "original_price": "£0",
                "saving_percent": 100,
                "type": "scraped_mse",
                "code": "",
                "steps": ["Read the full MSE article",
                          "Follow the deal link"],
                "timeFrame": "Check article",
                "source": "MoneySavingExpert",
                "last_updated": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S")
            })
        print(f"MSE: found {len(deals)} deals")
        return deals
    except Exception as e:
        print(f"MSE scrape failed: {e}")
        return []


# ============================================
# SUPERMARKET DEALS
# ============================================

def get_supermarket_deals() -> List[Dict]:
    """Supermarket deals with stacked prices"""
    return [
        {"store": "Tesco", "item": "Clubcard Prices - Selected Items", "deal_price": "Up to 50% off", "link": "https://www.tesco.com/clubcard/prices/", "original_price": "Varies", "saving_percent": 50, "base_price": 20},
        {"store": "Tesco", "item": "Fresh Meat & Fish", "deal_price": "£7.00", "link": "https://www.tesco.com/groceries/en-GB/shop/fresh-food/all", "original_price": "£10.00", "saving_percent": 30, "base_price": 7},
        {"store": "Asda", "item": "Payday Deals - Selected Items", "deal_price": "Up to 40% off", "link": "https://www.asda.com/deals", "original_price": "Varies", "saving_percent": 40, "base_price": 15},
        {"store": "Asda", "item": "Fresh Fruit & Vegetables", "deal_price": "£2.50", "link": "https://groceries.asda.com/deals/fresh-food", "original_price": "£3.50", "saving_percent": 29, "base_price": 2.5},
        {"store": "Sainsbury's", "item": "Nectar Prices - Members Only", "deal_price": "Exclusive prices", "link": "https://www.sainsburys.co.uk/nectar-prices", "original_price": "Varies", "saving_percent": 25, "base_price": 12},
        {"store": "Sainsbury's", "item": "Meal Deal - Lunch", "deal_price": "£3.50", "link": "https://www.sainsburys.co.uk/meal-deal", "original_price": "£5.00", "saving_percent": 30, "base_price": 3.5},
        {"store": "Iceland", "item": "3 for £10 - Selected Frozen", "deal_price": "£10.00", "link": "https://www.iceland.co.uk/offers", "original_price": "£15.00", "saving_percent": 33, "base_price": 10},
        {"store": "Iceland", "item": "Family Favourites Bundle", "deal_price": "£8.00", "link": "https://www.iceland.co.uk/family-meals", "original_price": "£12.00", "saving_percent": 33, "base_price": 8}
    ]


# ============================================
# CALCULATE STACKED PRICE
# ============================================

def calculate_stacked_price(deal: Dict) -> float:
    """Calculate real price after stacking discounts"""
    store = deal["store"]
    base_price = deal.get("base_price", 0)
    
    if base_price == 0 and "£" in str(deal.get("deal_price", "")):
        match = re.search(r'£(\d+(?:\.\d{2})?)', str(deal["deal_price"]))
        if match:
            base_price = float(match.group(1))
    
    if base_price == 0:
        return 0
    
    stacking_rate = STACKING_RATES.get(store, 4.0)
    savings = base_price * (stacking_rate / 100)
    return round(base_price - savings, 2)


# ============================================
# MAIN SCRAPER FUNCTION
# ============================================

def run_all_scrapers() -> Dict:
    """Run all scrapers and save results"""
    print("🛒 Money Hunters Scraper Starting...")
    print("=" * 50)
    
    all_deals = []
    
    # Get manual offers (30+)
    print("\n📦 Fetching manual offers (bank switches, referrals, cashback)...")
    manual_offers = get_manual_offers()
    all_deals.extend(manual_offers)
    print(f"   Found {len(manual_offers)} manual offers")
    
    # Get supermarket deals
    print("\n📦 Fetching supermarket deals...")
    supermarket_deals = get_supermarket_deals()
    all_deals.extend(supermarket_deals)
    print(f"   Found {len(supermarket_deals)} supermarket deals")
    
    # Scrape Reddit r/beermoneyuk
    print("\n📡 Scraping Reddit r/beermoneyuk...")
    reddit_deals = scrape_reddit_beermoneyuk()
    time.sleep(2)
    
    # Scrape MoneySavingExpert RSS
    print("\n📡 Scraping MoneySavingExpert RSS...")
    mse_deals = scrape_mse_rss()
    
    scraped = reddit_deals + mse_deals
    
    # Deduplicate against manual offers
    manual_stores = {o["store"].lower()[:8] for o in manual_offers}
    unique_scraped = [
        d for d in scraped
        if not any(d["store"].lower()[:8] in s 
                   for s in manual_stores)
    ]
    
    all_deals.extend(unique_scraped)
    
    # Calculate stacked prices for all deals
    for deal in all_deals:
        if deal["store"] in STACKING_RATES:
            stacked_price = calculate_stacked_price(deal)
            deal["stacked_price"] = stacked_price
            deal["best_payment_method"] = BEST_PAYMENT.get(deal["store"], "Gift card + loyalty")
            deal["stacking_rate"] = STACKING_RATES.get(deal["store"], 4.0)
        else:
            deal["stacked_price"] = 0
            deal["best_payment_method"] = "N/A"
            deal["stacking_rate"] = 0
        
        deal["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Sort by stacked price (cheapest first)
    all_deals.sort(key=lambda x: x.get("stacked_price", 999) if x.get("stacked_price", 0) > 0 else 999)
    
    # Save all deals to JSON
    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_deals": len(all_deals),
        "manual_count": len(manual_offers),
        "supermarket_count": len(supermarket_deals),
        "reddit_count": len(reddit_deals),
        "mse_count": len(mse_deals),
        "unique_scraped_count": len(unique_scraped),
        "sources": ["Manual", "Supermarket", "Reddit r/beermoneyuk", "MSE RSS"],
        "stacking_rates": STACKING_RATES,
        "deals": all_deals
    }
    
    with open("all_deals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Write scrape log
    log = [
        f"Scrape run: {datetime.now()}",
        f"Manual offers: {len(manual_offers)}",
        f"Supermarket deals: {len(supermarket_deals)}",
        f"Reddit deals: {len(reddit_deals)}",
        f"MSE deals: {len(mse_deals)}",
        f"Unique scraped: {len(unique_scraped)}",
        f"Total written: {len(all_deals)}",
    ]
    with open("scrape_log.txt", "w") as f:
        f.write("\n".join(log))
    
    print("-" * 40)
    print(f"✅ Total deals found: {len(all_deals)}")
    print(f"   - Manual offers: {len(manual_offers)}")
    print(f"   - Supermarket deals: {len(supermarket_deals)}")
    print(f"   - Reddit deals: {len(reddit_deals)}")
    print(f"   - MSE deals: {len(mse_deals)}")
    print(f"   - Unique scraped: {len(unique_scraped)}")
    print(f"💾 Saved to all_deals.json")
    print(f"📝 Log written to scrape_log.txt")
    
    return output


# ============================================
# RUN THE SCRAPER
# ============================================

if __name__ == "__main__":
    run_all_scrapers()
