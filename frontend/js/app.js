/**
 * app.js – Core application: routing, movie cards, API calls, watchlist, particles
 */
const API = 'http://127.0.0.1:5000/api';
window.POSTERS_MAP = {};

// Fallback high-res poster fallback
const DEFAULT_POSTER = "https://image.111.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg";

// ── State ──────────────────────────────────────────────────────────
let currentPage = 'home';
let exploreCurrentPage = 1;
let explorePerPage = 20;
let selectedRating = 0;
let currentMovieId = null;
let userWatchlistIds = new Set();

// Load posters map for instantaneous resolution
fetch('data/posters.json')
  .then(r => r.json())
  .then(data => { window.POSTERS_MAP = data; })
  .catch(() => {});

// ── Page Routing ───────────────────────────────────────────────────
function showPage(name) {
  if (name === 'logout') {
    doLogout();
  }

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

  const page = document.getElementById(`page-${name}`);
  const link = document.getElementById(`nav-${name}`);
  if (page) page.classList.add('active');
  if (link) link.classList.add('active');
  currentPage = name;
  window.scrollTo(0, 0);

  if (name === 'explore' && document.getElementById('explore-grid').children.length === 0) {
    loadGenres();
    loadExploreMovies(1);
  }
  if (name === 'recommendations') {
    loadRecommendationsPage();
  }
  if (name === 'watchlist') {
    loadWatchlistPage();
  }
}

// ── Utilities ──────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type} show`;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 3800);
}

function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
}

function escHtml(str) {
  return String(str || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function getGenreGradient(genre = '') {
  const g = String(genre).toLowerCase();
  if (g.includes('action') || g.includes('adventure')) {
    return ['#e50914', '#1f0d10', '#0a0a0f', '🔥'];
  } else if (g.includes('sci-fi') || g.includes('fantasy')) {
    return ['#00d2ff', '#0a1931', '#060a12', '🚀'];
  } else if (g.includes('crime') || g.includes('thriller') || g.includes('mystery')) {
    return ['#ff9900', '#1c1306', '#09080a', '🔍'];
  } else if (g.includes('horror')) {
    return ['#ff2a5f', '#2a0812', '#050204', '👁️'];
  } else if (g.includes('animation')) {
    return ['#a855f7', '#1a0b2e', '#07030d', '✨'];
  } else if (g.includes('romance') || g.includes('comedy')) {
    return ['#ec4899', '#240a1a', '#0a0408', '💖'];
  } else if (g.includes('drama') || g.includes('biography') || g.includes('history')) {
    return ['#eab308', '#231c07', '#080703', '🎭'];
  }
  return ['#6366f1', '#13112c', '#06060f', '🎬'];
}

function generateMoviePosterSvg(title = 'Movie', genre = 'Cinema', year = '') {
  const [accent, bgMid, bgDark, icon] = getGenreGradient(genre);
  const cleanTitle = String(title || 'Movie').replace(/[<>&"]/g, '');
  const cleanGenre = String(genre || 'Cinema').replace(/[<>&"]/g, '');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="500" height="750" viewBox="0 0 500 750">
    <defs>
      <linearGradient id="g_${encodeURIComponent(cleanTitle).slice(0,6)}" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="${accent}" stop-opacity="0.45"/>
        <stop offset="50%" stop-color="${bgMid}" stop-opacity="0.95"/>
        <stop offset="100%" stop-color="${bgDark}"/>
      </linearGradient>
      <linearGradient id="o_${encodeURIComponent(cleanTitle).slice(0,6)}" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0%" stop-color="#050811" stop-opacity="0.98"/>
        <stop offset="55%" stop-color="#050811" stop-opacity="0.4"/>
        <stop offset="100%" stop-color="#050811" stop-opacity="0.05"/>
      </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#g_${encodeURIComponent(cleanTitle).slice(0,6)})"/>
    <circle cx="250" cy="240" r="140" fill="${accent}" opacity="0.12"/>
    <circle cx="250" cy="240" r="100" fill="none" stroke="${accent}" stroke-width="2" stroke-opacity="0.3" stroke-dasharray="6 6"/>
    <text x="250" y="275" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="90" text-anchor="middle" fill="#ffffff" opacity="0.95">${icon}</text>
    <rect width="100%" height="100%" fill="url(#o_${encodeURIComponent(cleanTitle).slice(0,6)})"/>
    <g transform="translate(36, 560)">
      <rect x="0" y="-32" width="68" height="24" rx="6" fill="${accent}" opacity="0.9"/>
      <text x="34" y="-16" font-family="'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="bold" text-anchor="middle" fill="#ffffff">${year || 'FILM'}</text>
      <text x="0" y="20" font-family="'Outfit', -apple-system, sans-serif" font-size="28" font-weight="800" fill="#ffffff">${cleanTitle.length > 20 ? cleanTitle.slice(0, 18) + '…' : cleanTitle}</text>
      <text x="0" y="52" font-family="'Segoe UI', Roboto, sans-serif" font-size="15" font-weight="600" fill="${accent}" opacity="0.95">${cleanGenre}</text>
    </g>
  </svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

function getMoviePoster(movie) {
  if (movie.poster_url && movie.poster_url.startsWith('http') && !movie.poster_url.includes('unsplash') && !movie.poster_url.includes('example')) {
    return movie.poster_url;
  }
  if (window.POSTERS_MAP && window.POSTERS_MAP[movie.movie_id]) {
    return window.POSTERS_MAP[movie.movie_id];
  }
  return generateMoviePosterSvg(movie.title, movie.genre, movie.year);
}

// ── Movie Card Builder with REAL Posters ───────────────────────────
function buildMovieCard(movie, extraBadge = '') {
  const card = document.createElement('div');
  card.className = 'movie-card';
  card.id = `card-${movie.movie_id}`;
  card.onclick = () => openMovieModal(movie.movie_id);

  const scoreHtml = extraBadge
    ? `<div class="score-badge">${extraBadge}</div>` : '';

  const ratingDisplay = movie.avg_rating
    ? `${parseFloat(movie.avg_rating).toFixed(1)}/10` : '—';

  const isBookmarked = userWatchlistIds.has(movie.movie_id);
  const bookmarkHtml = `
    <button class="bookmark-btn ${isBookmarked ? 'active' : ''}" title="Save to Watchlist" onclick="event.stopPropagation(); toggleWatchlist(${movie.movie_id})">
      ${isBookmarked ? '★' : '☆'}
    </button>
  `;

  const posterUrl = getMoviePoster(movie);
  const safeTitle = (movie.title || '').replace(/'/g, "\\'");
  const safeGenre = (movie.genre || '').replace(/'/g, "\\'");
  const safeYear = movie.year || '';

  card.innerHTML = `
    ${scoreHtml}
    ${bookmarkHtml}
    <div class="movie-card-poster">
      <img class="poster-img" src="${posterUrl}" alt="${escHtml(movie.title)}" loading="lazy" onerror="this.onerror=null; this.src=generateMoviePosterSvg('${safeTitle}', '${safeGenre}', '${safeYear}');" />
      <div class="poster-overlay"></div>
    </div>
    <div class="movie-card-body">
      <div class="movie-card-title" title="${escHtml(movie.title)}">${escHtml(movie.title)}</div>
      <div class="movie-card-genre">${escHtml(movie.genre || '')}</div>
      <div class="movie-card-rating">
        <span>⭐ ${ratingDisplay}</span>
        <span class="movie-card-year">${movie.year || ''}</span>
      </div>
    </div>`;
  return card;
}

// ── Home Page ─────────────────────────────────────────────────────
async function loadHomePage() {
  try {
    const trendResp = await fetch(`${API}/movies/?page=1&per_page=12&sort=rating_desc`);
    const trendData = await trendResp.json();
    const trendEl = document.getElementById('trending-movies');
    trendEl.innerHTML = '';
    (trendData.movies || []).slice(0, 10).forEach(m => trendEl.appendChild(buildMovieCard(m)));

    const topResp = await fetch(`${API}/movies/?page=2&per_page=12&sort=rating_desc`);
    const topData = await topResp.json();
    const topEl = document.getElementById('top-rated-movies');
    topEl.innerHTML = '';
    const sorted = [...(topData.movies || [])].sort((a, b) => b.avg_rating - a.avg_rating);
    sorted.slice(0, 10).forEach(m => topEl.appendChild(buildMovieCard(m)));

  } catch(e) {
    console.error('Failed to load home page:', e);
  }
}

// ── Explore Page ──────────────────────────────────────────────────
async function loadGenres() {
  try {
    const resp = await fetch(`${API}/movies/genres`);
    const data = await resp.json();
    const sel = document.getElementById('genre-filter');
    sel.innerHTML = '<option value="">All Genres</option>';
    (data.genres || []).forEach(g => {
      const opt = document.createElement('option');
      opt.value = g; opt.textContent = g;
      sel.appendChild(opt);
    });
  } catch(e) {}
}

async function loadExploreMovies(page = 1) {
  const search = document.getElementById('explore-search')?.value || '';
  const genre  = document.getElementById('genre-filter')?.value || '';
  const sort   = document.getElementById('sort-filter')?.value || 'rating_desc';
  const grid   = document.getElementById('explore-grid');
  grid.innerHTML = '<div class="spinner"></div>';

  try {
    const params = new URLSearchParams({
      page, per_page: explorePerPage,
      ...(search && { search }),
      ...(genre  && { genre }),
      ...(sort   && { sort }),
    });
    const resp = await fetch(`${API}/movies/?${params}`);
    const data = await resp.json();

    grid.innerHTML = '';
    if (!data.movies || data.movies.length === 0) {
      grid.innerHTML = '<p style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-secondary)">No movies match your filters.</p>';
      return;
    }

    data.movies.forEach(m => grid.appendChild(buildMovieCard(m)));
    exploreCurrentPage = data.page || page;
    buildPagination(data.total_pages || 1, exploreCurrentPage);
  } catch(e) {
    grid.innerHTML = `<p style="color:var(--rose);padding:2rem;text-align:center">Error loading catalogue from database.</p>`;
  }
}

function buildPagination(totalPages, current) {
  const el = document.getElementById('pagination');
  el.innerHTML = '';
  if (totalPages <= 1) return;

  const range = [];
  for (let i = Math.max(1, current-2); i <= Math.min(totalPages, current+2); i++) range.push(i);
  if (range[0] > 1) { addPageBtn(el, 1, current); if (range[0] > 2) el.appendChild(Object.assign(document.createElement('span'), {textContent:'…', style:'padding:0 4px;color:var(--text-muted)'})); }
  range.forEach(p => addPageBtn(el, p, current));
  if (range.at(-1) < totalPages) { el.appendChild(Object.assign(document.createElement('span'), {textContent:'…', style:'padding:0 4px;color:var(--text-muted)'})); addPageBtn(el, totalPages, current); }
}

function addPageBtn(container, p, current) {
  const btn = document.createElement('button');
  btn.className = `page-btn${p === current ? ' active' : ''}`;
  btn.textContent = p;
  btn.onclick = () => loadExploreMovies(p);
  container.appendChild(btn);
}

// ── Watchlist Page ────────────────────────────────────────────────
async function loadWatchlistPage() {
  const uid = window.APP_USER_ID;
  const grid = document.getElementById('watchlist-grid');
  const emptyPrompt = document.getElementById('watchlist-empty');

  if (!uid) {
    grid.style.display = 'none';
    emptyPrompt.style.display = 'block';
    emptyPrompt.querySelector('h2').textContent = 'Sign In to View Watchlist';
    emptyPrompt.querySelector('p').textContent = 'Your saved movies will appear here once you sign in.';
    return;
  }

  grid.innerHTML = '<div class="spinner"></div>';
  grid.style.display = 'grid';
  emptyPrompt.style.display = 'none';

  try {
    const resp = await fetch(`${API}/users/${uid}/watchlist`, { headers: getAuthHeaders() });
    const data = await resp.json();
    grid.innerHTML = '';

    userWatchlistIds = new Set((data.watchlist || []).map(m => m.movie_id));

    if (!data.watchlist || data.watchlist.length === 0) {
      grid.style.display = 'none';
      emptyPrompt.style.display = 'block';
      emptyPrompt.querySelector('h2').textContent = 'Your Watchlist is Empty';
      emptyPrompt.querySelector('p').textContent = 'Explore movies and click the bookmark star to save your favorites here.';
      return;
    }

    data.watchlist.forEach(m => grid.appendChild(buildMovieCard(m)));
  } catch(e) {
    grid.innerHTML = '<p style="color:var(--rose);padding:2rem">Failed to load watchlist.</p>';
  }
}

async function toggleWatchlist(movieId) {
  const uid = window.APP_USER_ID;
  if (!uid) {
    toast('Please sign in to save movies to your watchlist', 'info');
    showPage('login');
    return;
  }

  try {
    const resp = await fetch(`${API}/users/${uid}/watchlist`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ movie_id: movieId }),
    });
    const data = await resp.json();
    if (resp.ok) {
      if (data.in_watchlist) {
        userWatchlistIds.add(movieId);
        toast('Added to your watchlist! ⭐', 'success');
      } else {
        userWatchlistIds.delete(movieId);
        toast('Removed from watchlist', 'info');
      }
      document.querySelectorAll(`#card-${movieId} .bookmark-btn`).forEach(btn => {
        btn.classList.toggle('active', data.in_watchlist);
        btn.textContent = data.in_watchlist ? '★' : '☆';
      });
      if (currentPage === 'watchlist') {
        loadWatchlistPage();
      }
    }
  } catch(e) {
    toast('Failed to update watchlist', 'error');
  }
}

// ── Movie Detail Modal with Authentic Posters ─────────────────────
async function openMovieModal(movieId) {
  currentMovieId = movieId;
  document.getElementById('movie-modal-content').innerHTML = '<div class="spinner"></div>';
  document.getElementById('movie-modal').classList.add('open');

  try {
    const [mResp, sResp] = await Promise.all([
      fetch(`${API}/movies/${movieId}`),
      fetch(`${API}/movies/${movieId}/similar?top_k=6`),
    ]);
    const movie   = await mResp.json();
    const simData = await sResp.json();
    renderMovieModal(movie, simData.similar || []);
  } catch(e) {
    document.getElementById('movie-modal-content').innerHTML =
      `<p style="color:var(--rose);text-align:center;padding:2rem">Failed to load movie details.</p>`;
  }
}

function renderMovieModal(movie, similar) {
  const genres = (movie.genre || '').split('|').map(g => g.trim()).filter(Boolean);
  const posterUrl = getMoviePoster(movie);

  const simHtml = similar.map(s => {
    const sPoster = getMoviePoster(s);
    return `
      <div class="similar-card" onclick="closeModal('movie-modal');openMovieModal(${s.movie_id})">
        <div class="similar-poster">
          <img src="${sPoster}" alt="${escHtml(s.title)}" onerror="this.onerror=null; this.src='${DEFAULT_POSTER}';" />
        </div>
        <div class="title">${escHtml(s.title)}</div>
      </div>`;
  }).join('');

  const starHtml = [1,2,3,4,5].map(i =>
    `<span class="star" id="star-${i}" onclick="setRating(${i})" onmouseover="hoverStar(${i})" onmouseout="resetStars()">☆</span>`
  ).join('');

  const isSaved = userWatchlistIds.has(movie.movie_id);

  document.getElementById('movie-modal-content').innerHTML = `
    <div class="movie-detail-grid">
      <div class="movie-detail-poster-wrap">
        <img class="modal-poster-img" src="${posterUrl}" alt="${escHtml(movie.title)}" onerror="this.onerror=null; this.src='${DEFAULT_POSTER}';" />
      </div>
      <div class="movie-detail-info">
        <h2 class="movie-detail-title">${escHtml(movie.title)}</h2>
        <div class="movie-detail-meta">
          ${genres.map(g => `<span class="meta-pill genre">${escHtml(g)}</span>`).join('')}
          <span class="meta-pill year">📅 ${movie.year || '—'}</span>
          <span class="meta-pill rating">⭐ ${parseFloat(movie.avg_rating||0).toFixed(1)}/10</span>
          <span class="meta-pill">🗣️ ${escHtml(movie.language || 'English')}</span>
        </div>
        <p class="movie-detail-overview">${escHtml(movie.overview || 'No description available for this title.')}</p>
        <div class="movie-detail-crew">
          <div class="crew-item"><label>Director</label><span>${escHtml(movie.director || '—')}</span></div>
          <div class="crew-item"><label>Starring Cast</label><span>${escHtml(movie.cast || '—')}</span></div>
          <div class="crew-item"><label>Movie ID</label><span>#${movie.movie_id}</span></div>
          <div class="crew-item"><label>Cloud DB</label><span>Neon PostgreSQL</span></div>
        </div>
        
        <div class="modal-actions-row">
          <div>
            <p style="font-size:0.8rem;color:var(--text-secondary);margin-bottom:0.35rem">Rate Film:</p>
            <div class="star-rating">${starHtml}</div>
          </div>
          <div style="margin-left:auto;display:flex;gap:8px">
            <button class="btn-secondary" onclick="toggleWatchlist(${movie.movie_id})">
              ${isSaved ? '★ In Watchlist' : '☆ Add to Watchlist'}
            </button>
            <button class="btn-primary" onclick="submitRating()">Submit</button>
          </div>
        </div>
      </div>
    </div>

    ${similar.length ? `<div class="similar-section" style="margin-top:2rem"><h3>✨ Semantically Similar Movies (TF-IDF Cosine)</h3><div class="similar-row">${simHtml}</div></div>` : ''}
  `;
}

function hoverStar(n) {
  for (let i = 1; i <= 5; i++) {
    const s = document.getElementById(`star-${i}`);
    if (s) s.textContent = i <= n ? '★' : '☆';
  }
}
function resetStars() {
  for (let i = 1; i <= 5; i++) {
    const s = document.getElementById(`star-${i}`);
    if (s) s.textContent = i <= selectedRating ? '★' : '☆';
  }
}
function setRating(n) {
  selectedRating = n;
  resetStars();
  for (let i = 1; i <= n; i++) {
    const s = document.getElementById(`star-${i}`);
    if (s) { s.textContent = '★'; s.classList.add('active'); }
  }
}

async function submitRating() {
  const userId = window.APP_USER_ID;
  if (!userId) {
    toast('Please sign in first to submit ratings', 'error');
    showPage('login');
    return;
  }
  if (!selectedRating) {
    toast('Please select a star rating (1–5)', 'error');
    return;
  }
  if (!currentMovieId) return;

  try {
    const resp = await fetch(`${API}/users/${userId}/rate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ movie_id: currentMovieId, rating: selectedRating * 1.0 }),
    });
    const data = await resp.json();
    if (resp.ok) {
      toast(`Rated ${selectedRating}★ – Synced to Neon DB! 🎉`, 'success');
      closeModal('movie-modal');
    } else {
      toast(data.error || 'Failed to submit rating', 'error');
    }
  } catch(e) {
    toast('Failed to record rating. Server error.', 'error');
  }
}

// ── Global Search ─────────────────────────────────────────────────
document.getElementById('global-search').addEventListener('input', function() {
  const q = this.value.trim();
  if (q.length >= 2) {
    showPage('explore');
    document.getElementById('explore-search').value = q;
    loadExploreMovies(1);
  }
});

// ── Explore search/filter listeners ──────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  loadHomePage();

  window.addEventListener('scroll', () => {
    document.getElementById('navbar').classList.toggle('scrolled', window.scrollY > 10);
  });

  let exploreSearchTimer;
  document.getElementById('explore-search')?.addEventListener('input', () => {
    clearTimeout(exploreSearchTimer);
    exploreSearchTimer = setTimeout(() => loadExploreMovies(1), 400);
  });
  document.getElementById('genre-filter')?.addEventListener('change', () => loadExploreMovies(1));
});

// ── Particle Animation ────────────────────────────────────────────
function initParticles() {
  const container = document.getElementById('particles');
  if (!container) return;
  for (let i = 0; i < 25; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.cssText = `
      left: ${Math.random()*100}%;
      bottom: -10px;
      animation-duration: ${4 + Math.random()*6}s;
      animation-delay: ${Math.random()*6}s;
      width: ${2 + Math.random()*3}px;
      height: ${2 + Math.random()*3}px;
      opacity: ${0.3 + Math.random()*0.7};
    `;
    container.appendChild(p);
  }
}

function handleGetRecs() {
  if (window.APP_USER_ID) {
    showPage('recommendations');
  } else {
    showPage('login');
  }
}
