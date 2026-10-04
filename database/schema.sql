-- CineMatch Database Schema
-- Production-Ready for Neon PostgreSQL & SQLite

CREATE TABLE IF NOT EXISTS cm_users (
    user_id         INTEGER PRIMARY KEY,
    username        VARCHAR(80)  UNIQUE,
    email           VARCHAR(120) UNIQUE,
    password_hash   VARCHAR(255),
    favorite_genres VARCHAR(255),
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cm_movies (
    movie_id    INTEGER      PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    year        INTEGER,
    genre       VARCHAR(200),
    director    VARCHAR(200),
    cast        TEXT,
    keywords    TEXT,
    overview    TEXT,
    language    VARCHAR(50)  DEFAULT 'English',
    avg_rating  REAL         DEFAULT 0.0,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cm_ratings (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER   NOT NULL REFERENCES cm_users(user_id) ON DELETE CASCADE,
    movie_id    INTEGER   NOT NULL REFERENCES cm_movies(movie_id) ON DELETE CASCADE,
    rating      REAL      NOT NULL CHECK(rating BETWEEN 0.5 AND 5.0),
    timestamp   INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

CREATE TABLE IF NOT EXISTS cm_watch_history (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER   NOT NULL REFERENCES cm_users(user_id) ON DELETE CASCADE,
    movie_id    INTEGER   NOT NULL REFERENCES cm_movies(movie_id) ON DELETE CASCADE,
    watched_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    watch_pct   REAL      DEFAULT 100.0
);

CREATE TABLE IF NOT EXISTS cm_watchlist (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER   NOT NULL REFERENCES cm_users(user_id) ON DELETE CASCADE,
    movie_id    INTEGER   NOT NULL REFERENCES cm_movies(movie_id) ON DELETE CASCADE,
    added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

-- Optimized Indexes
CREATE INDEX IF NOT EXISTS idx_cm_ratings_user    ON cm_ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_cm_ratings_movie   ON cm_ratings(movie_id);
CREATE INDEX IF NOT EXISTS idx_cm_history_user    ON cm_watch_history(user_id);
CREATE INDEX IF NOT EXISTS idx_cm_watchlist_user  ON cm_watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_cm_movies_genre    ON cm_movies(genre);
