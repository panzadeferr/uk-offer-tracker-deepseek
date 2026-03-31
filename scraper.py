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
                
                # Check if this is a megathread/guide post
                is_megathread = ("megathread" in title.lower() or 
                                "guide" in title.lower() or 
                                "guide" in flair.lower())
                
                if is_megathread:
                    # Parse structured megathread content
                    megathread_deals = parse_megathread_content(title, body)
                    deals.extend(megathread_deals)
                else:
                    # Regular post processing (existing logic)
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


def parse_megathread_content(title, body):
    """Parse structured megathread posts to extract individual offers"""
    import re
    deals = []
    
    # Split body into lines
    lines = body.split('\n')
    
    # Patterns for identifying offer lines
    list_item_pattern = re.compile(r'^[•\-\*]\s+(.*)', re.IGNORECASE)
    numbered_item_pattern = re.compile(r'^\d+[\.\)]\s+(.*)', re.IGNORECASE)
    bold_section_pattern = re.compile(r'\*\*(.*?)\*\*', re.IGNORECASE)
    
    current_category = "other"
    category_keywords = {
        "bank_switch": ["bank", "switch", "lloyds", "chase", "monzo", "revolut", 
                       "first direct", "halifax", "natwest", "nationwide", 
                       "barclays", "santander", "tsb", "co-operative"],
        "investment": ["invest", "share", "freetrade", "robinhood", "plum", 
                      "webull", "wealthify", "moneybox", "pension", "stocks"],
        "cashback": ["cashback", "topcashback", "quidco", "rakuten", "airtime", 
                    "cheddar", "jam doughnut", "everup", "gift card"],
        "utilities": ["energy", "octopus", "lebara", "sim", "mobile", "utility"],
        "travel": ["train", "travel", "trainpal", "flight", "hotel"],
        "business": ["business", "tide", "worldfirst", "account"],
        "freebies": ["free", "costa", "waitrose", "coffee", "cake"]
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip paragraphs and guides (lines that are too long or contain explanations)
        if len(line) > 200 or ":" in line and "http" not in line:
            continue
        
        # Check if line is a list item
        list_match = list_item_pattern.match(line)
        numbered_match = numbered_item_pattern.match(line)
        
        if not list_match and not numbered_match:
            continue
        
        # Extract the offer text
        offer_text = list_match.group(1) if list_match else numbered_match.group(1)
        
        # Identify offer name (look for bold text or first few words before £)
        offer_name = ""
        bold_match = bold_section_pattern.search(offer_text)
        if bold_match:
            offer_name = bold_match.group(1).strip()
        else:
            # Take first 3-5 words as offer name
            words = offer_text.split()
            if len(words) > 5:
                offer_name = " ".join(words[:5])
            else:
                offer_name = offer_text
        
        # Extract first valid £ value (not highest)
        amounts = re.findall(r'£(\d+(?:\.\d{2})?)', offer_text)
        if not amounts:
            continue
        
        # Filter unrealistic totals (ignore combined earnings like £1450+)
        valid_amounts = []
        for amount in amounts:
            try:
                amount_float = float(amount)
                # Skip unrealistic totals (combined earnings)
                if amount_float > 1000:
                    continue
                # Skip very small amounts (likely not main reward)
                if amount_float < 5:
                    continue
                valid_amounts.append(amount_float)
            except ValueError:
                continue
        
        if not valid_amounts:
            continue
        
        # Take the first valid amount (not the highest)
        reward_amount = valid_amounts[0]
        reward = f"£{reward_amount:.2f}"
        
        # Determine category
        category = "other"
        offer_lower = offer_text.lower()
        for cat, keywords in category_keywords.items():
            if any(keyword in offer_lower for keyword in keywords):
                category = cat
                break
        
        # Extract link if present
        link_match = re.search(r'https?://[^\s\)]+', offer_text)
        link = link_match.group(0) if link_match else ""
        
        # Create deal object
        deal = {
            "store": offer_name[:40],
            "item": offer_text[:80],
            "deal_price": reward,
            "link": link,
            "original_price": "£0",
            "saving_percent": 100,
            "type": "scraped_reddit",
            "code": "",
            "steps": ["Read the Reddit post for full details",
                      "Follow the referral link",
                      "Complete the required steps"],
            "timeFrame": "Varies",
            "source": "r/beermoneyuk",
            "reddit_score": 0,  # Will be set by parent function
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category
        }
        
        deals.append(deal)
    
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

def scrape_google_news_deals():
    import xml.etree.ElementTree as ET
    import re
    deals = []
    queries = [
        "UK bank switch bonus referral 2026",
        "UK cashback free share bonus offer 2026"
    ]
    
    action_words = ["switch", "referral", "cashback", "bonus", 
                    "free share", "sign up", "refer", "open account"]
    noise_words = ["opinion", "analysis", "podcast", "explainer",
                   "what is", "how does", "history of", "review of",
                   "results", "earnings", "profits", "shares fall",
                   "shares rise", "stock", "market"]
    
    for query in queries:
        try:
            q = query.replace(" ", "+")
            url = (
                "https://news.google.com/rss/search"
                f"?q={q}&hl=en-GB&gl=GB&ceid=GB:en"
            )
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            
            item_count = 0
            for item in items:
                if item_count >= 10:  # Limit to 10 results per query
                    break
                    
                title = item.findtext("title","")
                link = item.findtext("link","")
                desc = item.findtext("description","")
                combined = (title+" "+desc).lower()
                
                # Must contain £ symbol with a number
                if not re.search(r'£\d+(?:\.\d{2})?', combined):
                    continue
                
                # Must contain at least one action word
                if not any(action in combined for action in action_words):
                    continue
                
                # Must NOT contain noise words
                if any(noise in combined for noise in noise_words):
                    continue
                
                # Extract reward amount
                amounts = re.findall(r'£(\d+(?:\.\d{2})?)', title+" "+desc)
                if not amounts:
                    continue
                
                # Minimum reward filter: only include if reward >= £5
                try:
                    reward_amount = float(amounts[0])
                    if reward_amount < 5:
                        continue
                except ValueError:
                    continue
                
                reward = f"£{amounts[0]}"
                
                deals.append({
                    "store": title[:40],
                    "item": title[:80],
                    "deal_price": reward,
                    "link": link,
                    "original_price": "£0",
                    "saving_percent": 100,
                    "type": "scraped_mse",
                    "code": "",
                    "steps": [
                        "Read the full article",
                        "Follow the deal link",
                        "Complete required steps"
                    ],
                    "timeFrame": "Check article",
                    "source": "Google News",
                    "last_updated": datetime.now()
                        .strftime("%Y-%m-%d %H:%M:%S")
                })
                item_count += 1
                
            time.sleep(1)
        except Exception as e:
            print(f"Google News query failed: {e}")
    print(f"Google News: found {len(deals)} deals")
    return deals

def scrape_hotukdeals():
    from bs4 import BeautifulSoup
    import re
    deals = []
    urls = [
        "https://www.hotukdeals.com/deals/financial",
        "https://www.hotukdeals.com/search?q=bank+switch",
        "https://www.hotukdeals.com/search?q=cashback+referral"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            print(f"HotUKDeals {url[-20:]}: {r.status_code}")
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.content, 'html.parser')
            # Find deal articles
            articles = soup.find_all('article', limit=20)
            for article in articles:
                title_el = article.find(['h2','h3','a'])
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                link_el = article.find('a', href=True)
                link = link_el['href'] if link_el else url
                if not link.startswith('http'):
                    link = 'https://www.hotukdeals.com' + link
                combined = title.lower()
                keywords = ["switch","cashback","referral",
                           "bonus","free","bank","£","reward"]
                if not any(k in combined for k in keywords):
                    continue
                amounts = re.findall(
                    r'£(\d+(?:\.\d{2})?)', title)
                reward = f"£{amounts[0]}" if amounts else "Deal"
                if not amounts:
                    continue
                deals.append({
                    "store": title[:40],
                    "item": title[:80],
                    "deal_price": reward,
                    "link": link,
                    "original_price": "£0",
                    "saving_percent": 100,
                    "type": "scraped_hotukdeals",
                    "code": "",
                    "steps": [
                        "Check the HotUKDeals post",
                        "Follow the deal link",
                        "Complete required steps"
                    ],
                    "timeFrame": "Check post",
                    "source": "HotUKDeals",
                    "last_updated": datetime.now()
                        .strftime("%Y-%m-%d %H:%M:%S")
                })
            time.sleep(2)
        except Exception as e:
            print(f"HotUKDeals failed: {e}")
            continue
    # Deduplicate
    seen = set()
    unique = []
    for d in deals:
        key = d["store"][:20].lower()
        if key not in seen:
            seen.add(key)
            unique.append(d)
    print(f"HotUKDeals: found {len(unique)} deals")
    return unique


def scrape_megalist():
    import re
    deals = []
    headers = {
        "User-Agent": "MoneyHuntersUK/1.0 "
                      "(contact: hello@moneyhunters.co.uk)"
    }
    megalist_url = (
        "https://www.reddit.com/r/beermoneyuk/comments/"
        "1rywry0/the_beermoney_megalist_march_2026_"
        "the_big_list_of/.json"
    )
    try:
        r = requests.get(
            megalist_url, headers=headers, timeout=15)
        print(f"Megalist status: {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        post = data[0]["data"]["children"][0]["data"]
        body = post.get("selftext", "")
        lines = body.split("\n")
        for line in lines:
            line = line.strip()
            if not line or len(line) > 200:
                continue
            if "£" not in line:
                continue
            amounts = re.findall(
                r'£(\d+(?:\.\d{2})?)', line)
            if not amounts:
                continue
            amount = float(amounts[0])
            if amount < 5 or amount > 1000:
                continue
            # Skip explanatory sentences
            words = line.split()
            if len(words) > 15:
                continue
            # Clean store name from markdown
            clean = re.sub(
                r'\[|\]|\*\*|\*|#{1,3}|'
                r'[-•>]|\(http\S+\)', 
                '', line
            ).strip()
            store_words = clean.split()
            store = " ".join(store_words[:3])
            store = re.sub(
                r'£\d+|[\(\)]', '', store).strip()
            if len(store) < 2:
                continue
            # Extract URL
            url_match = re.search(
                r'https?://[^\s\)\]]+', line)
            offer_url = (
                url_match.group(0) if url_match
                else "https://www.reddit.com/r/"
                     "beermoneyuk/comments/1rywry0/"
            )
            # Clean URL
            offer_url = offer_url.rstrip('.,)')
            # Category detection
            line_lower = line.lower()
            if any(w in line_lower for w in [
                'bank','switch','cass',
                'current account','halifax',
                'lloyds','natwest','barclays',
                'santander','hsbc','first direct'
            ]):
                category = 'bank'
            elif any(w in line_lower for w in [
                'invest','share','stock','isa',
                'pension','freetrade','robinhood',
                'trading','webull','wealthify'
            ]):
                category = 'invest'
            elif any(w in line_lower for w in [
                'cashback','topcashback','quidco',
                'rakuten'
            ]):
                category = 'cashback'
            elif any(w in line_lower for w in [
                'gift','card','supermarket',
                'jam','airtime','cheddar'
            ]):
                category = 'gift'
            else:
                category = 'freebie'
            deals.append({
                "store": store[:40],
                "item": line[:80],
                "deal_price": f"£{amounts[0]}",
                "link": offer_url,
                "original_price": "£0",
                "saving_percent": 100,
                "type": "megalist",
                "category": category,
                "code": "",
                "steps": [
                    "Check the BeermoneyUK megalist",
                    "Follow the offer link",
                    "Complete required steps"
                ],
                "timeFrame": "Varies",
                "source": "BeermoneyUK Megalist",
                "last_updated": datetime.now()
                    .strftime("%Y-%m-%d %H:%M:%S")
            })
        # Deduplicate
        seen = set()
        unique = []
        for d in deals:
            key = d["store"].lower()[:8]
            if key not in seen:
                seen.add(key)
                unique.append(d)
        print(f"Megalist: found {len(unique)} deals")
        return unique
    except Exception as e:
        print(f"Megalist failed: {e}")
        return []


def scrape_scrimpr():
    from bs4 import BeautifulSoup
    import re
    deals = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0;"
                      " Win64; x64) AppleWebKit/537.36"
    }
    url = "https://scrimpr.co.uk/free-money-offers-uk/"
    try:
        r = requests.get(
            url, headers=headers, timeout=15)
        print(f"Scrimpr status: {r.status_code}")
        if r.status_code != 200:
            print(f"Scrimpr blocked: {r.status_code}")
            return []
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Find offer cards - Scrimpr uses div with class "so-card"
        offer_cards = soup.find_all('div', class_='so-card')
        print(f"Scrimpr cards found: {len(offer_cards)}")
        
        for card in offer_cards[:50]:  # Limit to 50 cards
            # Get offer name from data-name attribute or h3
            offer_name = card.get('data-name', '')
            if not offer_name:
                name_elem = card.find('h3', class_='so-card-platform-name')
                if name_elem:
                    offer_name = name_elem.get_text(strip=True)
            
            # Get reward value from data-value attribute
            reward_value = card.get('data-value', '')
            if not reward_value:
                # Try to extract from reward grid
                reward_elem = card.find(class_=lambda x: x and 'reward' in str(x).lower())
                if reward_elem:
                    reward_text = reward_elem.get_text(strip=True)
                    amounts = re.findall(r'£(\d+(?:\.\d{2})?)', reward_text)
                    if amounts:
                        reward_value = amounts[0]
            
            # Skip if no name or reward
            if not offer_name or not reward_value:
                continue
            
            # Get category from data-category attribute
            category = card.get('data-category', '').lower()
            if not category:
                category_tag = card.find(class_='so-card-type-tag')
                if category_tag:
                    category = category_tag.get_text(strip=True).lower()
            
            # Get link
            link_elem = card.find('a', href=True)
            link = link_elem['href'] if link_elem else url
            if link.startswith('/'):
                link = 'https://scrimpr.co.uk' + link
            
            # Get description from card text
            card_text = card.get_text(separator=' ', strip=True)
            description = card_text[:150] if len(card_text) > 150 else card_text
            
            # Map Scrimpr categories to our categories
            if 'bank' in category or 'switch' in category:
                deal_type = 'bank_switch'
            elif 'invest' in category:
                deal_type = 'invest'
            elif 'cashback' in category:
                deal_type = 'cashback'
            elif 'supermarket' in category or 'food' in category:
                deal_type = 'supermarket'
            elif 'utility' in category or 'energy' in category:
                deal_type = 'utilities'
            elif 'travel' in category:
                deal_type = 'travel'
            elif 'business' in category:
                deal_type = 'business'
            else:
                deal_type = 'other'
            
            # Create deal object
            try:
                reward_float = float(reward_value)
                if reward_float < 5 or reward_float > 1000:
                    continue
            except ValueError:
                continue
            
            deals.append({
                "store": offer_name[:40],
                "item": description[:80],
                "deal_price": f"£{reward_value}",
                "link": link,
                "original_price": "£0",
                "saving_percent": 100,
                "type": "scrimpr",
                "category": deal_type,
                "code": "",
                "steps": [
                    "Read the full offer on Scrimpr",
                    "Follow the referral link",
                    "Complete required steps"
                ],
                "timeFrame": "Check page",
                "source": "Scrimpr",
                "last_updated": datetime.now()
                    .strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Deduplicate
        seen = set()
        unique = []
        for d in deals:
            key = d["store"].lower()[:10] + d["deal_price"]
            if key not in seen:
                seen.add(key)
                unique.append(d)
        
        print(f"Scrimpr: found {len(unique)} deals")
        return unique
    except Exception as e:
        print(f"Scrimpr failed: {e}")
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

def clean_store_name(store: str) -> str:
    """Clean store names by removing truncation and cleaning up text"""
    # Remove truncation markers (trailing spaces followed by lowercase letter)
    store = re.sub(r'\s+[a-z]$', '', store)
    # Remove trailing punctuation
    store = re.sub(r'[.,;:]$', '', store)
    # Remove common news source suffixes
    suffixes = [' - Daily Express', ' - Metro', ' - which.co.uk', ' - Moneyfacts', 
                ' - Times & Sta', ' - The M', ' - Metro.co.uk']
    for suffix in suffixes:
        if store.endswith(suffix):
            store = store[:-len(suffix)].strip()
    # Capitalize first letter of each word
    return ' '.join(word.capitalize() for word in store.split())


def infer_category(deal: Dict) -> str:
    """Infer category based on store name and item description"""
    store_lower = deal["store"].lower()
    item_lower = deal.get("item", "").lower()
    type_lower = deal.get("type", "").lower()
    
    # Check store names first
    bank_keywords = ["lloyds", "chase", "monzo", "revolut", "first direct", "halifax", 
                     "natwest", "nationwide", "barclays", "santander", "tsb", "co-operative", "bank"]
    investment_keywords = ["freetrade", "robinhood", "plum", "webull", "wealthify", 
                          "moneybox", "ig", "invest", "share", "pension"]
    cashback_keywords = ["topcashback", "quidco", "rakuten", "airtime", "cheddar", 
                        "jam doughnut", "everup", "cashback"]
    supermarket_keywords = ["tesco", "sainsbury", "asda", "iceland", "morrisons", 
                           "waitrose", "aldi", "lidl", "supermarket", "grocer"]
    utility_keywords = ["octopus", "lebara", "energy", "sim", "mobile", "utility"]
    
    combined = store_lower + " " + item_lower + " " + type_lower
    
    if any(keyword in combined for keyword in bank_keywords):
        return "bank_switch"
    elif any(keyword in combined for keyword in investment_keywords):
        return "investment"
    elif any(keyword in combined for keyword in cashback_keywords):
        return "cashback"
    elif any(keyword in combined for keyword in supermarket_keywords):
        return "supermarket"
    elif any(keyword in combined for keyword in utility_keywords):
        return "utilities"
    elif "travel" in combined or "train" in combined:
        return "travel"
    elif "business" in combined:
        return "business"
    elif "free" in combined or "costa" in combined or "waitrose" in combined:
        return "freebies"
    else:
        return "other"


def validate_deal(deal: Dict) -> bool:
    """Validate deal has required fields and reasonable values"""
    required_fields = ["store", "item", "deal_price", "link"]
    for field in required_fields:
        if field not in deal or not deal[field]:
            return False
    
    # Validate deal price format
    deal_price = str(deal["deal_price"])
    if not re.search(r'£?\d+(?:\.\d{2})?', deal_price):
        return False
    
    # Validate link is a URL
    link = str(deal["link"])
    if not link.startswith(("http://", "https://")):
        return False
    
    return True


def run_all_scrapers() -> Dict:
    """Run all scrapers and save results with enhanced data integrity"""
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
    
    # Scrape Google News as MSE replacement - DISABLED for MegaList integration
    print("\n📡 Google News scraping DISABLED (using MegaList instead)...")
    news_deals = []  # Empty list instead of scraping
    
    # Scrape HotUKDeals
    print("\n📡 Scraping HotUKDeals...")
    hotuk_deals = scrape_hotukdeals()
    time.sleep(2)
    
    print("\n📡 Scraping BeermoneyUK Megalist...")
    megalist_deals = scrape_megalist()
    time.sleep(2)
    
    print("\n📡 Scraping Scrimpr...")
    scrimpr_deals = scrape_scrimpr()
    time.sleep(2)
    
    scraped = reddit_deals + news_deals + hotuk_deals + megalist_deals + scrimpr_deals
    # Clean and validate scraped deals
    cleaned_scraped = []
    for deal in scraped:
        # Clean store name
        if "store" in deal:
            deal["store"] = clean_store_name(deal["store"])
        
        # Add category if missing
        if "category" not in deal:
            deal["category"] = infer_category(deal)
        
        # Validate deal
        if validate_deal(deal):
            cleaned_scraped.append(deal)
        else:
            print(f"   Skipping invalid deal: {deal.get('store', 'Unknown')}")
    
    # Smart deduplication against manual offers
    manual_store_names = {o["store"].lower() for o in manual_offers}
    unique_scraped = []
    
    for deal in cleaned_scraped:
        deal_store_lower = deal["store"].lower()
        is_duplicate = False
        
        # Check for exact matches or partial matches
        for manual_store in manual_store_names:
            if (deal_store_lower == manual_store or 
                manual_store in deal_store_lower or 
                deal_store_lower in manual_store):
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_scraped.append(deal)
    
    all_deals.extend(unique_scraped)
    
    # Calculate stacked prices and add missing fields for all deals
    for deal in all_deals:
        # Ensure all deals have category
        if "category" not in deal:
            deal["category"] = infer_category(deal)
        
        # Ensure all deals have type (use category as fallback)
        if "type" not in deal:
            deal["type"] = deal["category"]
        
        # Clean store name if not already cleaned
        if "store" in deal:
            deal["store"] = clean_store_name(deal["store"])
        
        # Calculate stacked prices for supermarkets
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
    
    # Sort by stacked price (cheapest first), then by deal amount
    def get_sort_key(deal):
        # Try to extract numeric value from deal_price for sorting
        deal_price = str(deal.get("deal_price", "£0"))
        match = re.search(r'£?(\d+(?:\.\d{2})?)', deal_price)
        amount = float(match.group(1)) if match else 0
        
        stacked = deal.get("stacked_price", 999)
        if stacked > 0:
            return (stacked, -amount)  # Cheapest stacked first, then highest amount
        else:
            return (999, -amount)  # Non-stacked deals after stacked ones
    
    all_deals.sort(key=get_sort_key)
    
    # Save all deals to JSON
    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_deals": len(all_deals),
        "manual_count": len(manual_offers),
        "supermarket_count": len(supermarket_deals),
        "reddit_count": len(reddit_deals),
        "news_count": len(news_deals),
        "hotukdeals_count": len(hotuk_deals),
        "megalist_count": len(megalist_deals),
        "scrimpr_count": len(scrimpr_deals),
        "unique_scraped_count": len(unique_scraped),
        "sources": ["Manual", "Supermarket", "Reddit r/beermoneyuk", "Google News", "HotUKDeals", "BeermoneyUK Megalist", "Scrimpr"],
        "stacking_rates": STACKING_RATES,
        "deals": all_deals
    }
    
    with open("all_deals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # Write detailed scrape log
    log = [
        f"Scrape run: {datetime.now()}",
        f"Manual offers: {len(manual_offers)}",
        f"Supermarket deals: {len(supermarket_deals)}",
        f"Reddit deals: {len(reddit_deals)}",
        f"Google News deals: {len(news_deals)}",
        f"HotUKDeals deals: {len(hotuk_deals)}",
        f"Megalist deals: {len(megalist_deals)}",
        f"Scrimpr deals: {len(scrimpr_deals)}",
        f"Cleaned scraped: {len(cleaned_scraped)}",
        f"Unique scraped: {len(unique_scraped)}",
        f"Total written: {len(all_deals)}",
        f"Data quality: {len(cleaned_scraped)}/{len(scraped)} deals passed validation",
    ]
    with open("scrape_log.txt", "w") as f:
        f.write("\n".join(log))
    
    print("-" * 40)
    print(f"✅ Total deals found: {len(all_deals)}")
    print(f"   - Manual offers: {len(manual_offers)}")
    print(f"   - Supermarket deals: {len(supermarket_deals)}")
    print(f"   - Reddit deals: {len(reddit_deals)}")
    print(f"   - Google News deals: {len(news_deals)}")
    print(f"   - HotUKDeals deals: {len(hotuk_deals)}")
    print(f"   - Unique scraped: {len(unique_scraped)}")
    print(f"📊 Data quality: {len(cleaned_scraped)}/{len(scraped)} deals passed validation")
    print(f"💾 Saved to all_deals.json")
    print(f"📝 Log written to scrape_log.txt")
    
    return output


# ============================================
# RUN THE SCRAPER
# ============================================

if __name__ == "__main__":
    run_all_scrapers()
