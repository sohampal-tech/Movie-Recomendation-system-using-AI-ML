/**
 * auth.js – Authentication, JWT sessions, Login, Register, Logout, and User Profile
 */

window.APP_USER = null;
window.APP_USER_ID = null;
window.AUTH_TOKEN = null;

function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (window.AUTH_TOKEN) {
    headers['Authorization'] = `Bearer ${window.AUTH_TOKEN}`;
  }
  return headers;
}

// ── Auth Tab Switching ──────────────────────────────────────────────
function switchAuthTab(tab) {
  document.getElementById('tab-login-btn').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register-btn').classList.toggle('active', tab === 'register');
  document.getElementById('tab-login-content').classList.toggle('active', tab === 'login');
  document.getElementById('tab-register-content').classList.toggle('active', tab === 'register');

  const mainTitle = document.getElementById('auth-main-title');
  const mainSub   = document.getElementById('auth-main-sub');
  if (tab === 'login') {
    mainTitle.textContent = 'Welcome Back';
    mainSub.textContent = 'Sign in to access your custom AI movie recommendations and ratings.';
  } else {
    mainTitle.textContent = 'Join CineMatch';
    mainSub.textContent = 'Create your account to unlock AI-powered recommendations synced to Neon Cloud DB.';
  }
}

// ── Genre Pill Selector in Registration ─────────────────────────────
function toggleGenrePill(el) {
  el.classList.toggle('selected');
}

function getSelectedGenres() {
  const selected = [];
  document.querySelectorAll('#reg-genre-pills .genre-toggle.selected').forEach(el => {
    selected.push(el.dataset.genre);
  });
  return selected.join('|');
}

// ── Form Login (Email/Username + Password) ──────────────────────────
async function handleFormLogin(e) {
  e.preventDefault();
  const identifier = document.getElementById('signin-identifier').value.trim();
  const password   = document.getElementById('signin-password').value;
  const btn = document.getElementById('btn-signin-submit');

  if (!identifier || !password) {
    toast('Please enter your email/username and password', 'error');
    return;
  }

  btn.textContent = 'Signing in…';
  btn.disabled = true;

  try {
    const payload = identifier.includes('@')
      ? { email: identifier, password }
      : { username: identifier, password };

    const resp = await fetch(`${API}/users/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();

    if (resp.ok) {
      setSession(data.user, data.token);
      toast(data.message || 'Login successful!', 'success');
      showPage('recommendations');
    } else {
      toast(data.error || 'Login failed. Please check credentials.', 'error');
    }
  } catch (err) {
    toast('Cannot connect to server. Ensure Flask backend is running.', 'error');
  } finally {
    btn.textContent = 'Sign In to CineMatch';
    btn.disabled = false;
  }
}

// ── Quick Demo Login ────────────────────────────────────────────────
async function quickLoginDemo(userId) {
  try {
    toast(`Logging in as Demo User #${userId}…`, 'info');
    const resp = await fetch(`${API}/users/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
    });
    const data = await resp.json();

    if (resp.ok) {
      setSession(data.user, data.token);
      toast(`Signed in as ${data.user.username || `User #${userId}`} 🎉`, 'success');
      showPage('recommendations');
    } else {
      toast(data.error || 'Failed to login demo user', 'error');
    }
  } catch (e) {
    toast('Backend server unreachable', 'error');
  }
}

// ── Form Register ───────────────────────────────────────────────────
async function handleFormRegister(e) {
  e.preventDefault();
  const username = document.getElementById('reg-username').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const favorite_genres = getSelectedGenres();
  const btn = document.getElementById('btn-register-submit');

  if (!username || !email || !password) {
    toast('Please fill in all required fields', 'error');
    return;
  }

  btn.textContent = 'Creating Account…';
  btn.disabled = true;

  try {
    const resp = await fetch(`${API}/users/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, favorite_genres }),
    });
    const data = await resp.json();

    if (resp.ok) {
      setSession(data.user, data.token);
      toast(data.message || 'Account created successfully! 🎉', 'success');
      showPage('recommendations');
    } else {
      toast(data.error || 'Registration failed', 'error');
    }
  } catch (err) {
    toast('Server connection failed', 'error');
  } finally {
    btn.textContent = 'Create Account';
    btn.disabled = false;
  }
}

// ── Session Management ──────────────────────────────────────────────
function setSession(user, token) {
  window.APP_USER = user;
  window.APP_USER_ID = user.user_id;
  window.AUTH_TOKEN = token;

  localStorage.setItem('cm_user', JSON.stringify(user));
  localStorage.setItem('cm_user_id', user.user_id);
  if (token) localStorage.setItem('cm_token', token);

  updateUserUI(user);
}

function updateUserUI(user) {
  if (!user) {
    document.getElementById('user-display-name').textContent = 'Sign In';
    document.getElementById('user-avatar-icon').textContent = '👤';
    document.getElementById('user-pill-badge').style.display = 'none';
    document.getElementById('nav-login').textContent = 'Sign In';
    const ac = document.getElementById('alpha-control');
    if (ac) ac.style.display = 'none';
    return;
  }

  const name = user.username || `User #${user.user_id}`;
  document.getElementById('user-display-name').textContent = name;
  document.getElementById('user-avatar-icon').textContent = '🎬';
  document.getElementById('user-pill-badge').style.display = 'inline-block';
  document.getElementById('nav-login').textContent = 'Account';

  document.getElementById('drop-user-name').textContent = name;
  document.getElementById('drop-user-email').textContent = user.email || `ID: #${user.user_id}`;

  const ac = document.getElementById('alpha-control');
  if (ac) ac.style.display = 'flex';
}

function handleUserPillClick() {
  if (!window.APP_USER_ID) {
    showPage('login');
  } else {
    const drop = document.getElementById('user-dropdown');
    drop.classList.toggle('show');
  }
}

// Close user dropdown when clicking outside
document.addEventListener('click', (e) => {
  const container = document.getElementById('user-menu-container');
  if (container && !container.contains(e.target)) {
    document.getElementById('user-dropdown')?.classList.remove('show');
  }
});

// ── Logout ──────────────────────────────────────────────────────────
async function doLogout() {
  const lastUser = window.APP_USER?.username || `User #${window.APP_USER_ID || 'Guest'}`;
  document.getElementById('logout-last-user').textContent = lastUser;

  try {
    await fetch(`${API}/users/logout`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
  } catch(e) {}

  window.APP_USER = null;
  window.APP_USER_ID = null;
  window.AUTH_TOKEN = null;
  localStorage.removeItem('cm_user');
  localStorage.removeItem('cm_user_id');
  localStorage.removeItem('cm_token');

  updateUserUI(null);
  document.getElementById('user-dropdown')?.classList.remove('show');
  toast('You have successfully signed out.', 'info');
}

// ── Profile Modal ───────────────────────────────────────────────────
async function showUserProfileModal() {
  document.getElementById('user-dropdown')?.classList.remove('show');
  const uid = window.APP_USER_ID;
  if (!uid) { showPage('login'); return; }

  const modal = document.getElementById('profile-modal');
  const content = document.getElementById('profile-modal-content');
  content.innerHTML = '<div class="spinner"></div>';
  modal.classList.add('open');

  try {
    const resp = await fetch(`${API}/users/${uid}/profile`, { headers: getAuthHeaders() });
    const data = await resp.json();

    const genresHtml = Object.entries(data.top_genres || {})
      .map(([g, cnt]) => `<span class="meta-pill genre">${escHtml(g)} (${cnt})</span>`)
      .join(' ') || '<span style="color:var(--text-muted)">No ratings yet</span>';

    const recentHtml = (data.recently_rated || []).map(r => `
      <div style="display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid var(--glass-border)">
        <span>${escHtml(r.title)}</span>
        <span style="color:var(--amber);font-weight:600">${r.rating} ⭐</span>
      </div>
    `).join('') || '<p style="color:var(--text-muted);font-size:0.85rem">No recent ratings</p>';

    content.innerHTML = `
      <div style="text-align:center;margin-bottom:1.5rem">
        <div style="font-size:3rem;margin-bottom:0.5rem">👤</div>
        <h2 style="font-family:'Outfit',sans-serif;font-size:1.8rem;font-weight:800">${escHtml(data.username || `User #${uid}`)}</h2>
        <p style="color:var(--text-secondary);font-size:0.85rem">${escHtml(data.email || 'Neon PostgreSQL Member')}</p>
      </div>
      <div class="logout-stats-box" style="margin-bottom:1.5rem">
        <div class="logout-stat"><strong>${data.total_ratings || 0}</strong><span>Total Ratings</span></div>
        <div class="logout-stat"><strong>${data.avg_rating_given || 0} / 5.0</strong><span>Avg Rating Given</span></div>
        <div class="logout-stat"><strong>#${uid}</strong><span>Member ID</span></div>
      </div>
      <div style="margin-bottom:1.5rem">
        <h4 style="font-size:0.9rem;margin-bottom:0.5rem;color:var(--text-secondary)">Favorite Genres</h4>
        <div>${genresHtml}</div>
      </div>
      <div>
        <h4 style="font-size:0.9rem;margin-bottom:0.5rem;color:var(--text-secondary)">Recent Ratings</h4>
        <div>${recentHtml}</div>
      </div>
      <div style="margin-top:2rem;display:flex;gap:1rem;justify-content:flex-end">
        <button class="btn-secondary" onclick="closeModal('profile-modal')">Close</button>
        <button class="btn-primary" onclick="closeModal('profile-modal');showPage('recommendations')">View My Picks</button>
      </div>
    `;
  } catch (err) {
    content.innerHTML = `<p style="color:var(--rose)">Failed to load user profile.</p>`;
  }
}

// ── Restore Session on Startup ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const savedToken = localStorage.getItem('cm_token');
  const savedUser  = localStorage.getItem('cm_user');
  const savedUid   = localStorage.getItem('cm_user_id');

  if (savedUser) {
    try {
      window.APP_USER = JSON.parse(savedUser);
      window.APP_USER_ID = window.APP_USER.user_id;
      window.AUTH_TOKEN = savedToken;
      updateUserUI(window.APP_USER);
    } catch(e) {}
  } else if (savedUid) {
    window.APP_USER_ID = parseInt(savedUid, 10);
    window.APP_USER = { user_id: window.APP_USER_ID, username: `User #${window.APP_USER_ID}` };
    updateUserUI(window.APP_USER);
  }
});
