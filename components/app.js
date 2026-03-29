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
  loadOffers();
  loadProgress();
  setupEventListeners();
  updateUI();
  initAuth();
}

// Load offers from all_deals.json
// Note: The JSON file has "deals" key, not "offers" key
async function loadOffers() {
  try {
    const response = await fetch('all_deals.json');
    const data = await response.json();
    // The JSON file has "deals" key, not "offers" key
    state.offers = data.deals || [];
    console.log(`Loaded ${state.offers.length} offers`);
    renderAll();
  } catch (error) {
    console.error('Failed to load offers:', error);
    // Fallback to empty array
    state.offers = [];
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
  // Implementation would render offers to the UI
  const offersGrid = document.getElementById('offersGrid');
  if (offersGrid) {
    offersGrid.innerHTML = state.offers.map(offer => `
      <div class="offer-card" onclick="openOffer('${offer.id}')">
        <div class="offer-name">${offer.name}</div>
        <div class="reward">${formatMoney(offer.value || 0)}</div>
        <div class="offer-badge">${offer.badge || ''}</div>
      </div>
    `).join('');
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
  const offer = state.offers.find(o => o.id === offerId);
  if (!offer) return;
  
  document.getElementById('panelTitle').textContent = offer.name;
  document.getElementById('panelBody').innerHTML = `
    <div class="panel-section">
      <div class="panel-reward">${formatMoney(offer.value || 0)}</div>
      <div class="panel-desc">${offer.desc || ''}</div>
      <div class="panel-badge">${offer.badge || ''}</div>
    </div>
  `;
  
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