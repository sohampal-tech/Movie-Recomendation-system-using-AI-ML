/**
 * recommendations.js – Personalised recommendations, alpha control
 */

async function loadRecommendationsPage() {
  const grid  = document.getElementById('rec-grid');
  const prompt = document.getElementById('rec-login-prompt');
  const subtitle = document.getElementById('rec-subtitle');

  if (!window.APP_USER_ID) {
    if (prompt) prompt.style.display = 'block';
    if (grid) grid.style.display = 'none';
    return;
  }

  if (prompt) prompt.style.display = 'none';
  if (grid) {
    grid.style.display = 'grid';
    grid.innerHTML = '<div class="spinner"></div>';
  }
  
  const displayName = window.APP_USER?.username || `User #${window.APP_USER_ID}`;
  if (subtitle) subtitle.textContent = `AI Recommendations tailored for ${displayName}`;

  const alpha = document.getElementById('alpha-slider')?.value / 100 || 0.6;

  try {
    const resp = await fetch(
      `${API}/recommendations/user/${window.APP_USER_ID}?top_k=12&alpha=${alpha}`,
      { headers: getAuthHeaders() }
    );
    const data = await resp.json();

    if (!grid) return;
    grid.innerHTML = '';
    if (!data.recommendations || data.recommendations.length === 0) {
      grid.innerHTML = `<p style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-secondary)">No recommendations found yet. Try rating a few movies on the Explore tab!</p>`;
      return;
    }

    data.recommendations.forEach((rec, idx) => {
      const card = buildRecCard(rec, idx + 1);
      grid.appendChild(card);
    });

  } catch(e) {
    if (grid) grid.innerHTML = `<p style="color:var(--rose);padding:2rem;text-align:center">Failed to compute recommendations. Is the Flask server running?</p>`;
  }
}

function buildRecCard(rec, rank) {
  const card = document.createElement('div');
  card.className = 'movie-card rec-card';
  card.id = `rec-card-${rec.movie_id}`;
  card.onclick = () => openMovieModal(rec.movie_id);

  const scorePercent = Math.round(rec.hybrid_score * 100);
  const cfPercent    = Math.round(rec.collaborative_score * 100);
  const cbPercent    = Math.round(rec.content_score * 100);
  const ratingDisplay = rec.avg_rating ? parseFloat(rec.avg_rating).toFixed(1) : '—';
  const isBookmarked = userWatchlistIds.has(rec.movie_id);
  const posterUrl = getMoviePoster(rec);

  const safeTitle = (rec.title || '').replace(/'/g, "\\'");
  const safeGenre = (rec.genre || '').replace(/'/g, "\\'");
  const safeYear = rec.year || '';

  card.innerHTML = `
    <div class="score-badge">#${rank} Pick</div>
    <button class="bookmark-btn ${isBookmarked ? 'active' : ''}" title="Save to Watchlist" onclick="event.stopPropagation(); toggleWatchlist(${rec.movie_id})">
      ${isBookmarked ? '★' : '☆'}
    </button>
    <div class="movie-card-poster">
      <img class="poster-img" src="${posterUrl}" alt="${escHtml(rec.title)}" loading="lazy" onerror="this.onerror=null; this.src=generateMoviePosterSvg('${safeTitle}', '${safeGenre}', '${safeYear}');" />
      <div class="poster-overlay"></div>
    </div>
    <div class="movie-card-body">
      <div class="movie-card-title" title="${escHtml(rec.title)}">${escHtml(rec.title)}</div>
      <div class="movie-card-genre">${escHtml(rec.genre || '')}</div>
      <div class="movie-card-rating">
        <span>⭐ ${ratingDisplay}</span>
        <span style="color:var(--purple-light);font-weight:700">${scorePercent}% Match</span>
      </div>
    </div>

    <div class="score-bars" id="bars-${rec.movie_id}">
      <div style="display:flex;justify-content:space-between;font-size:0.72rem;color:var(--text-secondary);margin-bottom:5px">
        <span>Collaborative (CF): <strong>${cfPercent}%</strong></span>
        <span>Content (CB): <strong>${cbPercent}%</strong></span>
      </div>
      <div style="height:5px;background:rgba(255,255,255,0.08);border-radius:3px;overflow:hidden;display:flex">
        <div style="width:${cfPercent}%;background:var(--purple);height:100%" title="Collaborative Filtering Weight"></div>
        <div style="width:${cbPercent}%;background:var(--teal);height:100%" title="Content Semantics Weight"></div>
      </div>
    </div>
  `;
  return card;
}

function updateAlphaLabel(val) {
  const label = document.getElementById('alpha-label');
  if (label) {
    const v = parseInt(val, 10);
    label.textContent = `${v}% Collaborative / ${100 - v}% Content`;
  }
}

async function applyAlpha() {
  const slider = document.getElementById('alpha-slider');
  if (!slider) return;
  const alpha = parseInt(slider.value, 10) / 100;

  try {
    await fetch(`${API}/recommendations/alpha`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ alpha }),
    });
    toast(`AI Blend updated: ${Math.round(alpha*100)}% Collaborative / ${Math.round((1-alpha)*100)}% Content`, 'success');
    loadRecommendationsPage();
  } catch(e) {
    toast('Failed to update balance', 'error');
  }
}
