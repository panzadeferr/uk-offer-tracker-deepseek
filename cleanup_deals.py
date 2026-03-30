"""
Data Cleanup Script — Money Hunters UK
Phase 1B: Clean existing all_deals.json
- Strip markdown from malformed store/item names
- Remove prose/non-offer entries
- Re-assign categories correctly
- Fix bank vs supermarket categorization
"""

import json
import re
from datetime import datetime


# ============================================================
# CONFIG
# ============================================================

PROSE_PREFIXES = [
    "on the face of it",
    "but they have",
    "claim a ",
    "nx rewards: typically",
    "complete savings:",
    "free trial period",
    "cost: both platforms",
    "20% off a",
    "topcashback: free to",
    "spend",
    "total spent",
    "add a debit",
    "receive 1000",
    "try out zilch",
    "link:",
    "there is over",
    "in the first month",
    "karma vouchers occasionally",
]

PROSE_EXACT = [
    "total spent",
    "total spent after cashback",
]

# Banks that contain supermarket keywords — must NOT be filtered as supermarket
BANK_EXCEPTIONS = [
    "tesco bank",
    "sainsbury bank",
    "sainsburys bank",
    "m&s bank",
    "marks and spencer bank",
    "waitrose bank",
    "co-operative bank",
    "cooperative bank",
    "co operative bank",
]

# Supermarket keywords (only match if not a bank exception)
SUPERMARKET_KEYWORDS = ["tesco", "asda", "sainsbury", "iceland", "morrisons",
                         "waitrose", "aldi", "lidl", "co-op food"]

# Category mapping — checked in priority order
CATEGORY_MAP = [
    # Banks FIRST (before supermarkets)
    (["tesco bank", "sainsbury bank", "m&s bank", "marks spencer bank",
      "natwest", "lloyds", "barclays", "hsbc", "first direct", "co-operative bank",
      "cooperative bank", "tsb", "cahoot", "barclaycard", "mbna", "revolut",
      "monzo", "chase", "halifax", "santander", "starling", "metro bank",
      "virgin money"], "bank"),
    # Investments
    (["invest", "isa", "freetrade", "robinhood", "webull", "wealthify",
      "plum", "wealthyhood", "ig invest", "ig trading", "fidelity",
      "charles stanley", "quilter", "scottish friendly", "shepherds friendly",
      "beanstalk", "chip", "j.p. morgan", "nutmeg", "pensionbee",
      "moneybox", "prosper", "airwallex"], "invest"),
    # Cashback
    (["topcashback", "quidco", "rakuten", "cashback", "complete savings",
      "nx rewards", "swipii", "airtime rewards", "slide", "cheddar",
      "everup", "airtime", "airtime"], "cashback"),
    # Gift cards
    (["jam doughnut", "gift card", "one4all", "karma vouchers",
      "nx rewards", "argos voucher"], "gift"),
    # Crypto
    (["crypto.com", "wirex", "bitcoin", "crypto", "coinbase"], "earn"),
    # Business
    (["tide", "worldfirst", "airwallex", "world first"], "business"),
    # Travel
    (["octopus", "trainpal", "wise", "avios", "british airways",
      "currensea", "post office travel", "gohenry"], "travel"),
    # Earn online
    (["freecash", "swagbucks", "gemsloot", "cash in style", "outplayed",
      "earnlab", "adgem", "rubify"], "earn"),
    # Mobile
    (["lebara", "mobile", "sim", "airtime rewards"], "mobile"),
    # Supermarkets (checked AFTER banks)
    (["tesco", "asda", "sainsbury", "iceland", "morrisons",
      "waitrose", "aldi", "lidl"], "supermarket"),
]


# ============================================================
# HELPERS
# ============================================================

def strip_markdown(text: str) -> str:
    """Strip markdown formatting and normalize text."""
    if not text:
        return ""
    # Remove bold/italic: **text** or *text*
    text = re.sub(r'\*+([^*\n]+?)\*+', r'\1', text)
    # Remove markdown links: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
    # Remove everything after a pipe (table column separator)
    text = re.sub(r'\s*\|.*$', '', text, flags=re.DOTALL)
    # Remove HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # Remove emoji at start (common in markdown headings)
    text = re.sub(r'^[🌐📲💰✅🎁🔗⭐💳🏦📱🛒🚆✈️☕⚡🥦🥂🛵📦💄💸👤]+\s*', '', text)
    # Collapse multiple spaces
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def is_prose(cleaned_store: str) -> bool:
    """Return True if the CLEANED store name looks like prose (not an offer).
    Only call this on the already-stripped name, never on raw markdown.
    """
    name_lower = cleaned_store.lower()

    # Check known prose prefixes (already strips markdown)
    for prefix in PROSE_PREFIXES:
        # Strip leading ** from prefix for comparison too
        clean_prefix = re.sub(r'\*+', '', prefix).strip().lower()
        if name_lower.startswith(clean_prefix):
            return True

    # Check exact matches
    for exact in PROSE_EXACT:
        if name_lower == exact.lower():
            return True

    # More than 7 words in cleaned name = very likely prose sentence
    word_count = len(cleaned_store.split())
    if word_count > 7:
        return True

    # Ends with sentence-level punctuation (truncated prose)
    if cleaned_store.endswith(('...', '. ')):
        return True

    # Completely empty after cleaning
    if not cleaned_store.strip():
        return True

    return False


def assign_category(store_name: str, existing_category: str = None) -> str:
    """Assign correct category based on cleaned store name."""
    store_lower = store_name.lower()

    for keywords, category in CATEGORY_MAP:
        for keyword in keywords:
            if keyword in store_lower:
                return category

    # Fall back to existing category if it's a valid app category
    valid_categories = ["bank", "invest", "cashback", "gift", "business",
                        "earn", "mobile", "travel", "freebie", "supermarket"]
    if existing_category in valid_categories:
        return existing_category

    return "freebie"


def fix_store_name(raw_store: str) -> str:
    """Strip markdown and clean up a store name."""
    cleaned = strip_markdown(raw_store)
    # Remove unclosed leading ** or * (regex only strips matched pairs)
    cleaned = re.sub(r'^\*+', '', cleaned).strip()
    # Remove truncated markdown links like "([direct offer](https://www.revo"
    # These appear when the scraper truncated the raw text at 40 chars mid-link
    cleaned = re.sub(r'\s*\(\[.*', '', cleaned).strip()
    # Remove trailing parenthetical link artifacts like "(direct offer)", "(cashback offer on X)"
    # but keep parentheticals that are part of the brand name like "(was Nutmeg)"
    cleaned = re.sub(
        r'\s*\((direct offer|cashback offer|cashback|offer on|via |was advertised|nutsaboutmoney)[^)]*\)',
        '', cleaned, flags=re.IGNORECASE
    ).strip()
    # Remove " | Get" / " | Open" suffix patterns
    cleaned = re.sub(r'\s*\|\s*(Get|Open|Invest|Switch|Sign).*', '', cleaned, flags=re.IGNORECASE)
    # Remove trailing bare ( if orphaned
    cleaned = re.sub(r'\s*\($', '', cleaned).strip()
    # Trim to reasonable length
    cleaned = cleaned[:50].strip()
    return cleaned


# ============================================================
# MAIN CLEANUP
# ============================================================

def run_cleanup():
    print("=" * 55)
    print("🧹 MONEY HUNTERS DATA CLEANUP")
    print("=" * 55)

    # Load existing data
    with open("all_deals.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    deals = data.get("deals", [])
    print(f"📦 Loaded {len(deals)} deals")

    cleaned_deals = []
    removed_prose = []
    fixed_names = []
    category_changes = []

    for deal in deals:
        raw_store = deal.get("store", "")
        raw_item = deal.get("item", "")

        # ── STEP 1: Strip markdown from names ──
        clean_store = fix_store_name(raw_store)
        clean_item = strip_markdown(raw_item)

        # ── STEP 2: Reject prose entries ──
        # Only check the CLEANED store name — checking raw inflates word count
        # because markdown symbols (**,|,etc.) are counted as extra words
        if is_prose(clean_store):
            removed_prose.append({
                "original_store": raw_store,
                "cleaned_store": clean_store,
                "deal_price": deal.get("deal_price", "?")
            })
            continue

        # Track if name was fixed
        if clean_store != raw_store:
            fixed_names.append({
                "from": raw_store[:50],
                "to": clean_store
            })

        # ── STEP 3: Update the deal ──
        deal["store"] = clean_store
        deal["item"] = clean_item if clean_item else clean_store
        deal["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ── STEP 4: Re-assign category (after cleaning name) ──
        old_category = deal.get("category", "")
        new_category = assign_category(clean_store, old_category)

        if old_category != new_category:
            category_changes.append({
                "store": clean_store,
                "from": old_category,
                "to": new_category
            })

        deal["category"] = new_category

        cleaned_deals.append(deal)

    # ── SAVE ──
    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_deals": len(cleaned_deals),
        "manual_count": data.get("manual_count", 0),
        "supermarket_count": data.get("supermarket_count", 0),
        "megalist_count": data.get("megalist_count", 0),
        "cleaned_count": len(cleaned_deals),
        "sources": data.get("sources", ["Manual", "Supermarket", "MegaList"]),
        "deals": cleaned_deals
    }

    with open("all_deals.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── REPORT ──
    print(f"\n📊 RESULTS:")
    print(f"   ✅ Clean deals saved: {len(cleaned_deals)}")
    print(f"   🗑️  Prose entries removed: {len(removed_prose)}")
    print(f"   🔧  Store names fixed: {len(fixed_names)}")
    print(f"   🏷️  Categories re-assigned: {len(category_changes)}")

    if removed_prose:
        print(f"\n🗑️  REMOVED ENTRIES:")
        for r in removed_prose:
            print(f"   ✕ '{r['original_store'][:50]}' ({r['deal_price']})")

    if fixed_names:
        print(f"\n🔧  FIXED NAMES:")
        for f_item in fixed_names:
            print(f"   '{f_item['from'][:50]}' → '{f_item['to']}'")

    if category_changes:
        print(f"\n🏷️  CATEGORY CHANGES:")
        for c in category_changes:
            print(f"   '{c['store']}': '{c['from']}' → '{c['to']}'")

    print(f"\n💾 Saved to all_deals.json")
    print(f"✅ CLEANUP COMPLETE: {len(deals)} → {len(cleaned_deals)} deals")

    return output


if __name__ == "__main__":
    run_cleanup()
