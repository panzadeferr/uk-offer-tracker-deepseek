# MoneyHunterUk Memory Bank

## Project Overview
**MoneyHunterUk** is a UK referral deal tracker application that helps users find and track bank switches, cashback offers, investment bonuses, and supermarket deals. The project aims to be the "sharpest referral deal tracker" in the UK market.

### Core Value Proposition
- Track 46+ verified UK deals (bank switches, referrals, cashback)
- Supermarket deals with stacked prices (gift card + loyalty card stacking)
- Telegram notifications for new deals
- Free forever service

### Key Statistics (from landing page)
- £1,000+ potential from bank switches alone
- 46+ verified live offers
- Zero cost - free forever
- Users already making money monthly

## Architecture & Components

### 1. Frontend (Progressive Web App)
- **index.html**: Landing page with marketing content, signup form, and feature showcase
- **app.html**: Fully-featured PWA application with:
  - Mobile-first responsive design with light/dark theme support
  - Supabase authentication (signup/login/password reset)
  - Real-time progress tracking and synchronization
  - Interactive offer panels with step-by-step guides
  - Cashback battle table with live data from `all_deals.json`
  - Gamification system (XP, levels, streaks, leaderboard)
  - Pending payout tracker with countdown timers
  - Community integration (Reddit, Telegram, Ko-fi)
  - Email capture for weekly deal newsletters
  - PWA install prompts for native app experience
- **CSS/JS**: All styling and functionality embedded in HTML files
- **PWA Support**: manifest.json, service worker (sw.js), icons for installable app

### 2. Backend & Data Processing
- **scraper.py**: Python script that:
  - Collects 30+ manual offers (bank switches, referrals, cashback)
  - Fetches supermarket deals with stacked prices
  - Calculates optimal stacking rates per store
  - Saves data to `all_deals.json`
  - Supports Telegram notifications (optional)

### 3. Data Storage & Synchronization
- **all_deals.json**: Primary data store containing all offers with:
  - Store names, item descriptions, deal prices
  - Original prices, saving percentages
  - Stacked prices (after gift card + loyalty discounts)
  - Links, codes, steps, timeframes
  - Last updated timestamps
- **Supabase Integration**: Cloud database for:
  - User authentication and profiles
  - Progress synchronization across devices
  - Offer status tracking (pending/completed)
  - Pending payout management
  - Leaderboard data

### 4. Deployment & Automation
- **GitHub Actions Workflows**:
  - `.github/workflows/deploy.yml`: Comprehensive deployment pipeline with:
    - JavaScript syntax validation
    - Security checks for exposed secrets
    - Required file validation
    - Manifest.json validation
    - Automated deployment to GitHub Pages
  - `.github/workflows/scraper.yml`: Automated scraping schedule with:
    - Runs every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
    - Manual trigger capability
    - Telegram notification integration
    - Automatic commit and push of updated `all_deals.json`
- **PWA Configuration**: Service worker for offline functionality
- **GitHub Pages Hosting**: Static site hosting with automated CI/CD

## Key Data Structures

### Offer Types
1. **Bank Switches**: Lloyds (£250), Chase UK (£50), First Direct (£175), Halifax (£150), NatWest (£200)
2. **Investment Offers**: Freetrade, Robinhood, Plum, Webull, Wealthify, Moneybox
3. **Cashback Sites**: TopCashback, Quidco, Rakuten
4. **Gift Card Apps**: Airtime, Cheddar, Jam Doughnut, EverUp
5. **Business Accounts**: Tide, WorldFirst
6. **Utilities**: Octopus Energy, Lebara
7. **Freebies**: Costa, Waitrose
8. **Other**: Wise, AMEX, TrainPal, Zilch, Zopa, PensionBee

### Supermarket Stacking Rates
- Tesco: 5.3% (EverUp 4.9% + Clubcard)
- Sainsbury's: 4.4% (JamDoughnut 4.1% + Nectar)
- Asda: 4.5% (Airtime Rewards 4% + Asda Rewards)
- Iceland: 5.0% (TopCashback 3.5% + Bonus Card)
- Morrisons: 4.0% (Cheddar 3% + More Card)
- Waitrose: 3.5% (JamDoughnut 3.5% + MyWaitrose)
- Aldi/Lidl: 2.0% (no gift cards, cashback credit card)

## Technical Implementation Details

### Scraper Functionality (`scraper.py`)
- **Manual Offers**: Hardcoded list of 30+ offers with complete details
- **Supermarket Deals**: Pre-defined supermarket deals with base prices
- **Stacking Calculation**: `calculate_stacked_price()` applies store-specific stacking rates
- **Telegram Integration**: Optional notification system using environment variables
- **Data Persistence**: JSON output with sorting (cheapest stacked price first)

### Frontend Features (app.html)
- **Mobile-First PWA**: Progressive Web App with install capability
- **Authentication**: Full Supabase auth system (signup, login, password reset)
- **Offer Management**: Interactive panels with step-by-step guides, tips, and warnings
- **Progress Tracking**: Real-time XP, levels, streaks, and leaderboard
- **Cashback Battle Table**: Live comparison of supermarket stacking rates
- **Pending Payout Tracker**: Countdown timers for expected payouts
- **Daily Tasks**: Personalized daily money-making plans
- **Theme Support**: Light/dark mode toggle
- **Offline Capability**: Service worker for offline functionality
- **Email Integration**: Weekly deal newsletter signup via Brevo/Railway proxy

### Integration Points
- **Supabase**: User authentication, data synchronization, and cloud storage
- **Brevo Email Service**: Email capture for weekly newsletters via Railway proxy
- **Telegram Bot**: Optional notifications for new deals
- **Local Storage**: Offline data persistence with cloud sync
- **GitHub Pages**: Static site hosting with automated deployment

## Deployment & Hosting

### Current Setup
- Static site hosting (likely GitHub Pages or similar)
- Automated scraping via GitHub Actions
- JSON data file as primary data source
- PWA capabilities for app-like experience

### GitHub Actions
- **scraper.yml**: Scheduled scraping job
- **deploy.yml**: Deployment workflow

## Business & Growth Features

### User Engagement
- Gamification: Levels, badges, streaks, leaderboard
- Progress tracking: Earned amounts, pending payouts
- Daily Telegram alerts (8am schedule)
- Weekly deal digests via email

### Monetization Strategy
- Referral links (affiliate commissions)
- Ko-fi donations
- Free forever model (no subscription fees)

### Community Building
- Reddit community: r/ReferralHunterUK
- Telegram channel: @MoneyHunterUK
- Email newsletter

## Development Status & Roadmap

### Current State (Fully Functional)
- ✅ Landing page with marketing content and email capture
- ✅ Comprehensive scraper with 30+ manual offers and supermarket deals
- ✅ Fully-featured PWA application (app.html) with:
  - Supabase authentication and cloud sync
  - Interactive offer panels with step-by-step guides
  - Gamification system (XP, levels, streaks, leaderboard)
  - Cashback battle table with live data integration
  - Pending payout tracker with countdown timers
  - Daily personalized money-making plans
  - Light/dark theme support
  - PWA install capability
- ✅ GitHub Actions for automated scraping and deployment
- ✅ Email newsletter integration via Brevo/Railway
- ✅ Community integration (Reddit, Telegram, Ko-fi)

### Critical Issues Fixed (March 28, 2026)
1. **CRIT-01: Split app.html into components** - Completed: app.html now uses modular components in `/components/` directory
2. **CRIT-02: renderAll optimization** - Fixed: Implemented efficient rendering with proper state management
3. **CRIT-03: Sequential Supabase sync loop** - Fixed: Implemented proper async/await pattern for Supabase operations
4. **CRIT-04: Wire to all_deals.json** - Fixed: app.js now loads offers from all_deals.json with proper error handling
5. **CRIT-05: inferCategory improvement** - Fixed: Enhanced category inference with better regex patterns
6. **CRIT-06: offerEnrichment merge** - Fixed: Proper data merging between offers and user progress
7. **CRIT-07: formatMoney rounding** - Fixed: formatMoney() now properly rounds to 2 decimal places
8. **CRIT-09: leaderboard real data** - Fixed: Leaderboard now uses real user data from Supabase
9. **CRIT-11: swipe-down gesture** - Fixed: Added touch gesture support for mobile navigation
10. **CRIT-12: iOS keyboard fix** - Fixed: Improved iOS keyboard handling with viewport adjustments
11. **CRIT-13: skeleton loaders** - Fixed: Added skeleton loading states for better UX
12. **CRIT-15: Google Fonts display:swap** - Fixed: Added display=swap to Google Fonts for better performance

### Immediate Improvements Needed
1. **Data Freshness Automation**: Scraper needs to run regularly via GitHub Actions (currently manual setup)
2. **Offer Updates**: Manual offers need regular review and updates as bank switch offers change
3. **Testing**: Comprehensive testing of Supabase integration and PWA functionality
4. **Performance Optimization**: Code splitting and lazy loading for better mobile performance

### Future Enhancements
1. **Advanced Notifications**: Push notifications for payout dates and new offers
2. **Social Features**: Friend referrals, achievement sharing, community challenges
3. **Mobile Apps**: Native iOS/Android wrappers using Capacitor or similar
4. **API Development**: Public REST API for deal data access
5. **Browser Extension**: Real-time deal alerts while browsing shopping sites
6. **Advanced Analytics**: User earning insights and personalized recommendations
7. **Multi-language Support**: Expand beyond UK English market

## Technical Debt & Considerations

### Security
- API keys in scraper.py should use environment variables
- Email validation and spam protection needed
- Secure handling of user data

### Scalability
- Current JSON file approach won't scale with many users
- Need database for user accounts and tracking
- Caching strategy for deal data

### Maintenance
- Manual offers need regular updates
- Supermarket rates change frequently
- Bank switch offers expire/change

## Project Structure
```
MoneyHunterUk/
├── index.html              # Landing page
├── app.html               # Application dashboard (uses components)
├── components/            # Modular components
│   ├── header.html        # Header with stats and theme toggle
│   ├── footer.html        # Bottom navigation
│   ├── home-view.html     # Home screen components
│   ├── offers-view.html   # Offers listing and filtering
│   ├── stack-view.html    # Cashback battle and stacking guides
│   ├── progress-view.html # Progress tracking and profile
│   ├── community-view.html # Community and leaderboard
│   ├── modals.html        # Modals and drawers
│   └── app.js             # Main application JavaScript
├── scraper.py             # Data collection script
├── all_deals.json         # Generated deal data
├── memory_bank.md         # This file
├── manifest.json          # PWA manifest
├── sw.js                  # Service worker
├── requirements.txt       # Python dependencies
├── .github/workflows/
│   ├── deploy.yml         # Deployment pipeline
│   └── scraper.yml        # Scheduled scraping
├── icons/                 # PWA icons
│   ├── icon-192.png
│   ├── icon-512.png
│   └── icon-maskable.png
└── README.md              # Project documentation
```

## Team & Contact
- **Primary Contact**: hello@moneyhunters.co.uk
- **Reddit**: r/ReferralHunterUK
- **Telegram**: @MoneyHunterUK
- **Ko-fi**: ko-fi.com/moneyhunteruk

## Last Updated
- **Memory Bank Created**: March 27, 2026
- **Project Last Commit**: Based on git hash 581ce3642fc3e5d79b66e8afc5fb310a1d6e8c02
- **Data Freshness**: Scraper includes "updated March 2026" references

---

*This memory bank serves as a living document for the MoneyHunterUk project. Update regularly as the project evolves.*