# 🚀 CineMatch – Vercel Deployment Guide

A step-by-step production deployment guide for the **CineMatch Hybrid AI Movie Recommendation Platform** on [Vercel](https://vercel.com).

---

## 📋 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Prerequisites](#-prerequisites)
3. [Method 1: Full-Stack on Vercel (Recommended 1-Repo Setup)](#-method-1-full-stack-on-vercel)
4. [Method 2: Frontend on Vercel + Backend on Render/Railway](#-method-2-split-architecture-alternative)
5. [Environment Variables Reference](#-environment-variables-reference)
6. [Step-by-Step Vercel Dashboard Deployment](#-step-by-step-vercel-dashboard-deployment)
7. [Post-Deployment Verification](#-post-deployment-verification)
8. [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 🏗 Architecture Overview

| Layer | Technology | Hosting |
|---|---|---|
| **Frontend UI** | HTML5, Vanilla CSS3 (Glassmorphism), ES6+ JavaScript | Vercel Static Hosting (Edge CDN) |
| **Backend API** | Flask 2.3, Python 3.9/3.10, scikit-learn, TF-IDF | Vercel Serverless Functions (`api/index.py`) |
| **Database** | PostgreSQL with `cm_` schema isolation | [Neon Serverless PostgreSQL](https://neon.tech) |
| **Artwork CDN** | Official TMDB Images + Dynamic SVG Fallback Generator | TMDB CDN / Client-side SVG |

---

## 🔑 Prerequisites

1. **GitHub Repository**: Pushed to [sohampal-tech/Movie-Recomendation-system-using-AI-ML](https://github.com/sohampal-tech/Movie-Recomendation-system-using-AI-ML)
2. **Vercel Account**: Free account on [vercel.com](https://vercel.com)
3. **Neon PostgreSQL Database**: Active connection string from `.env`

---

## 📦 Method 1: Full-Stack on Vercel

Vercel natively supports Python WSGI apps using `vercel.json` routing.

### 1. Project Configuration Files

#### `vercel.json` (Create in repository root)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "backend/app.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/app.py"
    },
    {
      "src": "/css/(.*)",
      "dest": "/frontend/css/$1"
    },
    {
      "src": "/js/(.*)",
      "dest": "/frontend/js/$1"
    },
    {
      "src": "/data/(.*)",
      "dest": "/frontend/data/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/index.html"
    }
  ]
}
```

#### `api/index.py` (Serverless Entry Point Adapter)
```python
import sys
import os

# Add root directory to sys.path so modules import seamlessly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

app = create_app()

# Expose WSGI application for Vercel
if __name__ == "__main__":
    app.run()
```

#### `frontend/js/app.js` (Dynamic API Host Detection)
Ensure the frontend uses relative `/api` or the production domain in production:
```javascript
// Automatically switches between local Flask server and production Vercel deployment
const API = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://127.0.0.1:5000/api'
  : '/api';
```

---

## ⚙️ Environment Variables Reference

Add the following environment variables in the **Vercel Project Settings ➔ Environment Variables**:

| Variable Name | Required | Example Value | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | `postgresql+psycopg2://neondb_owner:***@ep-blue-math-ay6hko1f-pooler.c-5.us-east-2.aws.neon.tech:5432/neondb?sslmode=require` | Neon PostgreSQL pooled connection string |
| `SECRET_KEY` | **Yes** | `cinematch_super_secret_jwt_key_2026` | Session & Token cryptographic key |
| `JWT_SECRET_KEY` | **Yes** | `cinematch_super_secret_jwt_key_2026` | JWT Token signature key |
| `FLASK_ENV` | **Yes** | `production` | Enables production mode |
| `DB_TABLE_PREFIX` | Optional | `cm_` | Schema namespace prefix for tables |

---

## 🚀 Step-by-Step Vercel Dashboard Deployment

### Step 1: Import Project from GitHub
1. Open [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **"Add New..."** ➔ **"Project"**.
3. Connect your GitHub account and select `Movie-Recomendation-system-using-AI-ML`.

### Step 2: Configure Build & Output Settings
- **Framework Preset**: `Other`
- **Root Directory**: `./` (leave default)
- **Build Command**: `pip install -r requirements.txt` (or leave default)
- **Output Directory**: `frontend` (or leave default if using `vercel.json`)

### Step 3: Configure Environment Variables
Expand **"Environment Variables"** and add:
- `DATABASE_URL`
- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `FLASK_ENV` = `production`

### Step 4: Deploy
1. Click **"Deploy"**.
2. Vercel will build the serverless functions and distribute your frontend across global Edge CDN nodes in ~45 seconds.
3. You will receive your live URL (e.g. `https://cinematch-movie-recommender.vercel.app`).

---

## ⚡ Method 2: Split Architecture (Alternative)

If you prefer separating backend compute from edge frontend:

1. **Backend on Render / Railway**:
   - Create a Web Service on [Render](https://render.com) pointing to `backend/app.py`.
   - Start Command: `gunicorn backend.app:app`
   - Set environment variables (`DATABASE_URL`, `JWT_SECRET_KEY`).
2. **Frontend on Vercel**:
   - Deploy only the `frontend/` folder.
   - Point `const API = 'https://your-render-backend.onrender.com/api';` in `frontend/js/app.js`.

---

## ✅ Post-Deployment Verification

Once deployed, verify all features on your live Vercel URL:

- [ ] **Home Page**: Trending movies carousel and Top Rated masterworks load with genuine poster artwork.
- [ ] **Explore Catalogue**: Filter by genre, search by title, and sort by rating/year across all 200 distinct movies.
- [ ] **Authentication**: Register a new user (`POST /api/users/register`) and login (`POST /api/users/login`).
- [ ] **Recommendations Tab**: Adjust the Hybrid Alpha Slider (e.g., 70% Collaborative / 30% Content) and compute personalized picks.
- [ ] **Watchlist & Rating**: Bookmark movies to your watchlist and submit 1–10 star ratings with live database persistence.
- [ ] **Modal Detail View**: Click any card to inspect director, cast, synopsis, and similar film recommendations.

---

## 🛠 Troubleshooting & FAQs

### Q: Why do I get a 500 error on `/api/movies`?
**A:** Check the Vercel Runtime Logs. Ensure `DATABASE_URL` uses `postgresql+psycopg2://` with `?sslmode=require` for Neon PostgreSQL.

### Q: Why do some movie posters fail to render?
**A:** CineMatch features an automatic built-in SVG artwork generator fallback (`generateMoviePosterSvg`). If TMDB CDN is blocked on a visitor's network, every film automatically renders a distinct genre-gradient poster card with title and year metadata.

### Q: How do I redeploy after pushing updates to GitHub?
**A:** Vercel has continuous deployment enabled. Any `git push origin main` automatically triggers a zero-downtime rebuild and instant deployment.
