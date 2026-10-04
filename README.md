# 🎬 CineMatch — Hybrid Movie Recommender & Platform

> **AI-powered movie recommendation platform combining Collaborative Filtering (SVD) + Content-Based Filtering (TF-IDF + Cosine Similarity) with Cloud Neon PostgreSQL database synchronization and JWT Authentication.**

---

## 🌟 Key Features

- 🧠 **Hybrid AI Algorithm**: Weighted blending ($\alpha = 0.60$) of Collaborative Latent Matrix Factorisation (SVD) and Semantics (TF-IDF + Cosine Similarity).
- 🗄️ **Cloud Neon PostgreSQL Integration**: Seamlessly connects to Neon AWS PostgreSQL with fallback to SQLite for zero-downtime offline execution.
- 🔐 **Dedicated Login & Registration Pages**: Full account creation with favorite genre preference tagging, password hashing (`Werkzeug`), JWT session tokens, and instant 1-click Demo User profiles (`Alice #1`, `Bob #2`, `Carol #3`, `Demo User #42`).
- 🚪 **Dedicated Logout Page**: Visual session clearance confirmation, active account telemetry, and quick sign-in actions.
- 📑 **User Watchlist & Ratings**: Real-time bookmarking and 5-star rating updates that automatically feed back into recommendation weights.
- 🎨 **Modern Cyber-Cinema UI**: Fluid dark-mode interface with particle animations, circular confidence rings, responsive pagination, and genre search filters.

---

## 📁 Project Structure

```
hybrid-movie-recommender/
├── .env                        # PostgreSQL, JWT, SMTP & App configuration
├── requirements.txt            # Python dependencies
├── src/
│   ├── data/                   # DataLoader + DataPreprocessor
│   ├── content_based/          # TF-IDF vectoriser + Cosine Similarity
│   ├── collaborative/          # SVD Matrix Factorization + Predictions
│   ├── hybrid/                 # Hybrid Recommender (α-weighted blend)
│   ├── evaluation/             # RMSE, MAE, Precision@K, Recall@K, NDCG@K
│   └── utils/                  # Helpers (normalise, timers, logging)
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── database/               # Database connection (Neon PostgreSQL), ORM models, seeder
│   └── routes/                 # movies, recommendations, users blueprints
├── frontend/                   # HTML5 + Modern Vanilla CSS + JS SPA
│   ├── index.html              # Single Page Application views
│   ├── css/style.css           # Glassmorphic cyber-cinema design system
│   └── js/
│       ├── app.js              # Routing, movie grids, watchlists, modals
│       ├── auth.js             # JWT authentication, login, register, logout
│       └── recommendations.js  # Live recommendations & alpha sliders
├── database/
│   ├── schema.sql              # Neon PostgreSQL & SQLite schema
│   └── seed.sql                # Seed SQL data
└── tests/                      # 19 End-to-end and unit tests
```

---

## 🚀 Quick Start

### 1. Configure Environment (`.env`)

The project reads cloud database and JWT settings directly from `.env`:

```env
DB_HOST=ep-blue-math-ay6hko1f-pooler.c-5.us-east-2.aws.neon.tech
DB_PORT=5432
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=npg_9Hv6kjmnlOhb

JWT_SECRET=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=1440
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch CineMatch Server

```bash
python -m backend.app
```

Navigate to **`http://127.0.0.1:5000`** in your browser.

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/users/register` | Register new account (username, email, password, genres) |
| `POST` | `/api/users/login` | Login with credentials or User ID (returns JWT token) |
| `POST` | `/api/users/logout` | Acknowledge logout session termination |
| `GET`  | `/api/users/me` | Current authenticated user profile |
| `GET`  | `/api/users/<id>/profile` | User stats, ratings count, top genres |
| `GET`  | `/api/users/<id>/watchlist` | Retrieve user's saved movie watchlist |
| `POST` | `/api/users/<id>/watchlist` | Add/Remove movie from user watchlist |
| `POST` | `/api/users/<id>/rate` | Submit 0.5–5.0★ movie rating |
| `GET`  | `/api/movies/` | Paginated catalogue (search, genre filter, sorting) |
| `GET`  | `/api/movies/<id>` | Full movie details with crew & cast |
| `GET`  | `/api/movies/<id>/similar` | Content-similar movies via TF-IDF cosine score |
| `GET`  | `/api/recommendations/user/<id>` | Hybrid top-K recommendations for user |
| `POST` | `/api/recommendations/alpha` | Update $\alpha$ blend weight live |

---

## 🧪 Running Tests

```bash
python -m unittest discover tests
```
