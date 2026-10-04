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
