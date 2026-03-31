// Money Hunters UK - Main Application JavaScript

// Global state
let state = {
  offers: [],
  progress: {
    earned: 0,
    pending: 0,
    xp: 0,
    streak: 0,
    claims: 0,
    completed: 0,
    pendingCount: 0
  },
  user: null,
  theme: 'dark'
};

// Initialize the app
function initApp() {
  console.log('Money Hunters UK initializing...');
  (async () => {
    await loadOffersFromJSON();
    renderAll();
    initAuth();
    checkPasswordResetToken();
  })();
  loadProgress();
  setupEventListeners();
  updateUI();
}

// Load and filter scraped offers from all_deals.json
async function loadOffersFromJSON() {
  try {
    const res = await fetch(
      '/all_deals.json?v=' + Date.now()
    );
    if (!res.ok) throw new Error('fetch failed');
    const data = await res.json();
    if (!data.deals || !data.deals.length)
      throw new Error('no deals');
    
    const supermarkets = ['tesco','asda',
      'sainsbury','iceland','morrisons',
      'waitrose','aldi','lidl'];
    
    const scraped = data.deals.filter(d => {
      const s = (d.store||'').toLowerCase();
      const t = (d.type||'').toLowerCase();
      
      if (supermarkets.some(x => s.includes(x)))
        return false;
      
      return t==='scraped_reddit' ||
             t==='scraped_hotukdeals' ||
             t==='scraped_news' ||
             t==='megalist' ||
             t==='scrimpr' ||
             t==='bank_switch' ||
             t==='invest' ||
             t==='cashback' ||
             t==='referral' ||
             t==='business' ||
             t==='utilities' ||
             t==='pension' ||
             t==='credit';
    });
    
    if (!scraped.length) return;
    
    const existingIds = new Set(state.offers.map(o => o.id));
    
    const mapped = scraped.map(d => {
      const type = (d.type || '').toLowerCase();
      let badge;
      
      if (type === 'megalist') {
        badge = '🔥 BEERMONEY FIND';
      } else if (type === 'scrimpr') {
        badge = '💰 SCRIMPR DEAL';
      } else if (type === 'scraped_reddit') {
        badge = '🔥 REDDIT FIND';
      } else if (type === 'scraped_hotukdeals') {
        badge = '🏷️ HOTUKDEALS';
      } else {
        badge = '📋 DEAL';
      }
      
      return {
        id: (d.store||'offer')
              .toLowerCase()
              .replace(/\s+/g,'-')
              .replace(/[^a-z0-9-]/g,'')
              .slice(0,40)+'-scraped',
        name: (d.store||'New Offer').slice(0,40),
        category: d.category||'freebie',
        reward: d.deal_price||'Bonus',
        amount: parseFloat(
          String(d.deal_price||'0')
            .replace(/[^0-9.]/g,'')
        )||0,
        badge: badge,
        effort: 'Check source for details',
        desc: (d.item||d.store||'').slice(0,120),
        code: d.code||'',
        url: d.link||'#',
        steps: d.steps||[
          'Read the full offer details',
          'Follow the link to claim',
          'Complete required steps'
        ],
        expectedDays: 30,
        tips: ['Always verify current terms'],
        warnings: ['Details may change'],
        detailedSteps: d.steps||[]
      };
    });
    
    const newOffers = mapped.filter(
      o => !existingIds.has(o.id)
    );
    
    if (newOffers.length) {
      state.offers.push(...newOffers);
      console.log(
        'Loaded '+newOffers.length+
        ' fresh offers from all_deals.json'
      );
    }
  } catch(e) {
    console.log('Hardcoded offers only:',e.message);
  }
}

// Load progress from localStorage
function loadProgress() {
  const saved = localStorage.getItem('moneyhunters_progress');
  if (saved) {
    try {
      state.progress = JSON.parse(saved);
    } catch (e) {
      console.error('Failed to parse saved progress:', e);
    }
  }
}

// Save progress to localStorage
function saveState() {
  localStorage.setItem('moneyhunters_progress', JSON.stringify(state.progress));
  console.log('Progress saved');
  pushProgressToSupabase();
}

// Update UI with current state
function updateUI() {
  // Update stats
  document.getElementById('statSaved').textContent = formatMoney(state.progress.earned);
  document.getElementById('statPending').textContent = formatMoney(state.progress.pending);
  document.getElementById('statXp').textContent = state.progress.xp;
  document.getElementById('statStreak').textContent = `${state.progress.streak}🔥`;
  
  // Update plan amount
  const planAmount = calculatePlanAmount();
  document.getElementById('planAmount').textContent = formatMoney(planAmount);
  
  // Update profile section
  document.getElementById('earnedTotal').textContent = formatMoney(state.progress.earned);
  document.getElementById('pendingTotal').textContent = formatMoney(state.progress.pending);
  document.getElementById('activeTotal').textContent = state.progress.pendingCount;
  document.getElementById('profileClaims').textContent = state.progress.claims;
  document.getElementById('profileCompleted').textContent = state.progress.completed;
  document.getElementById('profilePendingCount').textContent = state.progress.pendingCount;
  document.getElementById('profileStreak').textContent = `${state.progress.streak}🔥`;
  
  // Calculate level
  const level = Math.floor(state.progress.xp / 50) + 1;
  const xpInLevel = state.progress.xp % 50;
  document.getElementById('profileLevel').textContent = `Level ${level}`;
  document.getElementById('profileXp').textContent = `${state.progress.xp} XP`;
  document.getElementById('xpCopy').textContent = `${xpInLevel} / 50 XP to next level`;
  document.getElementById('xpBar').style.width = `${(xpInLevel / 50) * 100}%`;
}

// Render all offers
function renderAll() {
  console.log('Rendering all offers');
  const offersGrid = document.getElementById('offersGrid');
  if (offersGrid) {
    offersGrid.innerHTML = state.offers.map((offer, index) => {
      // Use store and item fields from new scraper structure
      const offerName = offer.store || offer.name || 'Unknown Offer';
      const itemDesc = offer.item || offer.desc || '';
      const dealPrice = offer.deal_price || offer.value || '£0';
      const category = offer.category || 'other';
      const link = offer.link || '#';
      const steps = offer.step_by_step_guide || '';
      
      // Create a unique ID if not present
      const offerId = offer.id || `offer-${index}`;
      
      return `
        <div class="offer-card" onclick="openOffer('${offerId}')" data-category="${category}">
          <div class="offer-header">
            <div class="offer-name">${offerName}</div>
            <div class="reward">${dealPrice}</div>
          </div>
          <div class="offer-desc">${itemDesc.substring(0, 80)}${itemDesc.length > 80 ? '...' : ''}</div>
          <div class="offer-category">${category}</div>
          ${steps ? '<div class="offer-has-guide">🤖 AI Guide Available</div>' : ''}
        </div>
      `;
    }).join('');
    
    // Update offer count
    document.getElementById('offerCount').textContent = `${state.offers.length} offers`;
  }
}
// Calculate today's plan amount
function calculatePlanAmount() {
  // Simple calculation: sum of top 3 offers
  const topOffers = state.offers
    .filter(o => !o.completed && !o.pending)
    .sort((a, b) => (b.value || 0) - (a.value || 0))
    .slice(0, 3);
  
  return topOffers.reduce((sum, offer) => sum + (offer.value || 0), 0);
}

// Format money with £ symbol
function formatMoney(amount) {
  if (typeof amount !== 'number') amount = 0;
  return `£${amount.toFixed(2)}`;
}

// Toggle theme
function toggleTheme() {
  state.theme = state.theme === 'dark' ? 'light' : 'dark';
  document.body.classList.toggle('light');
  const toggleBtn = document.getElementById('themeToggle');
  toggleBtn.textContent = state.theme === 'dark' ? '🌙' : '☀️';
  saveState();
}

// Show auth modal
function showAuthModal() {
  document.getElementById('authModal').style.display = 'flex';
}

// Switch auth tab
function switchAuthTab(tab) {
  // Implementation for auth tabs
  console.log('Switching to auth tab:', tab);
}

// Handle signup
function handleSignup() {
  // Implementation for signup
  console.log('Signup handler');
}

// Handle login
function handleLogin() {
  // Implementation for login
  console.log('Login handler');
}

// Claim daily XP
function claimDaily() {
  state.progress.xp += 10;
  state.progress.streak += 1;
  saveState();
  updateUI();
  showToast('🎉 +10 XP added!');
}

// Open offer panel
function openPanel(offerId) {
  // Find offer by index if it's a generated ID
  let offer;
  if (offerId.startsWith('offer-')) {
    const index = parseInt(offerId.replace('offer-', ''));
    offer = state.offers[index];
  } else {
    offer = state.offers.find(o => o.id === offerId);
  }
  
  if (!offer) return;
  
  // Use new scraper structure fields
  const offerName = offer.store || offer.name || 'Unknown Offer';
  const itemDesc = offer.item || offer.desc || '';
  const dealPrice = offer.deal_price || offer.value || '£0';
  const link = offer.link || '#';
  const category = offer.category || 'other';
  const steps = offer.step_by_step_guide || '';
  const requirements = offer.requirements || '';
  
  document.getElementById('panelTitle').textContent = offerName;
  
  let panelHTML = `
    <div class="panel-section">
      <div class="panel-reward">${dealPrice}</div>
      <div class="panel-desc">${itemDesc}</div>
      <div class="panel-category">${category}</div>
  `;
  
  if (link && link !== '#') {
    panelHTML += `
      <a href="${link}" target="_blank" class="panel-link">
        🔗 Open Offer Link
      </a>
    `;
  }
  
  panelHTML += `</div>`;
  
  if (requirements) {
    panelHTML += `
      <div class="panel-section">
        <h4>Requirements:</h4>
        <div class="panel-requirements">${requirements.substring(0, 200)}${requirements.length > 200 ? '...' : ''}</div>
      </div>
    `;
  }
  
  if (steps) {
    panelHTML += `
      <div class="panel-section">
        <h4>🤖 AI Step-by-Step Guide:</h4>
        <div class="panel-guide">${steps.replace(/\n/g, '<br>')}</div>
      </div>
    `;
  }
  
  document.getElementById('panelBody').innerHTML = panelHTML;
  document.getElementById('offerPanel').classList.add('open');
}
// Open offer
function openOffer(offerId) {
  console.log('Opening offer:', offerId);
  openPanel(offerId);
}

// Close panel
function closePanel() {
  document.getElementById('offerPanel').classList.remove('open');
}

// Supabase functions
function pushProgressToSupabase() {
  console.log('Pushing progress to Supabase');
  // Implementation for Supabase sync
}

function pullProgressFromSupabase() {
  console.log('Pulling progress from Supabase');
  // Implementation for Supabase sync
}

function initAuth() {
  console.log('Initializing auth');
  // Implementation for auth initialization
}

// Check password reset token from URL
function checkPasswordResetToken() {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');
  if (token) {
    console.log('Password reset token detected:', token);
    // In a real implementation, you would validate the token
    // and show the password reset form
  }
}

// Show toast notification
function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);
  
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => {
      document.body.removeChild(toast);
    }, 300);
  }, 3000);
}

// Setup event listeners
function setupEventListeners() {
  // Theme toggle
  document.getElementById('themeToggle').addEventListener('click', toggleTheme);
  
  // Daily claim button
  document.getElementById('dailyBtn').addEventListener('click', claimDaily);
  
  // Panel close
  document.getElementById('panelClose').addEventListener('click', closePanel);
  
  // Navigation
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const view = btn.dataset.view;
      switchView(view);
      
      // Update active state
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
  
  // Brand home
  document.getElementById('brandHome').addEventListener('click', () => {
    switchView('home');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('.nav-btn[data-view="home"]').classList.add('active');
  });
}

// Switch view
function switchView(viewName) {
  document.querySelectorAll('.view').forEach(view => {
    view.classList.remove('active');
  });
  document.getElementById(`view-${viewName}`).classList.add('active');
}

// Expose functions to window for stub access
window.renderAllImpl = renderAll;
window.saveStateImpl = saveState;
window.openPanelImpl = openPanel;
window.closePanelImpl = closePanel;
window.handleSignupImpl = handleSignup;
window.handleLoginImpl = handleLogin;
window.pushProgressToSupabaseImpl = pushProgressToSupabase;
window.pullProgressFromSupabaseImpl = pullProgressFromSupabase;
window.initAuthImpl = initAuth;
window.claimDailyImpl = claimDaily;
window.openOfferImpl = openOffer;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);