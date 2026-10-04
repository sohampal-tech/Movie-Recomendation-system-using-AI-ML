"""
src/data/preprocess.py
Cleaning, normalisation, and feature engineering for movies + ratings.
Preserves authentic artwork poster URLs.
"""
import re
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from src.data.fetch_posters import CURATED_POSTERS

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Cleans raw dataframes and builds the feature matrix."""

    def __init__(self, processed_dir: str = "data/processed"):
        self.processed_dir = Path(processed_dir)
        try:
            self.processed_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._scaler = MinMaxScaler()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def preprocess_movies(self, movies_df: pd.DataFrame) -> pd.DataFrame:
        df = movies_df.copy()
        df = self._handle_missing(df)
        df = self._clean_text_fields(df)
        df = self._normalize_ratings(df)
        df = self._build_soup(df)
        try:
            df.to_csv(self.processed_dir / "movies_clean.csv", index=False)
            logger.info(f"Saved {len(df)} cleaned movies")
        except Exception as e:
            logger.debug(f"Skipping save (read-only): {e}")
        return df

    def preprocess_ratings(self, ratings_df: pd.DataFrame) -> pd.DataFrame:
        df = ratings_df.copy()
        df = df.drop_duplicates(subset=["user_id", "movie_id"])
        df = df.dropna(subset=["user_id", "movie_id", "rating"])
        df["rating"] = df["rating"].clip(0.5, 5.0)
        try:
            df.to_csv(self.processed_dir / "ratings_clean.csv", index=False)
            logger.info(f"Saved {len(df)} cleaned ratings")
        except Exception as e:
            logger.debug(f"Skipping save (read-only): {e}")
        return df

    def build_movie_features(self, movies_df: pd.DataFrame) -> pd.DataFrame:
        """Create feature matrix saved to movie_features.csv."""
        df = movies_df.copy()
        # One-hot encode primary genre
        primary_genre = df["genre"].apply(lambda g: g.split("|")[0] if pd.notna(g) else "Unknown")
        genre_dummies = pd.get_dummies(primary_genre, prefix="genre")
        features = pd.concat(
            [df[["movie_id", "avg_rating", "year"]], genre_dummies], axis=1
        )
        # Normalise numeric columns
        num_cols = ["avg_rating", "year"]
        features[num_cols] = self._scaler.fit_transform(features[num_cols].fillna(0))
        try:
            features.to_csv(self.processed_dir / "movie_features.csv", index=False)
            logger.info(f"Saved feature matrix with shape {features.shape}")
        except Exception as e:
            logger.debug(f"Skipping save (read-only): {e}")
        return features

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        df["title"] = df["title"].fillna("Unknown Title")
        df["genre"] = df["genre"].fillna("Unknown")
        df["director"] = df["director"].fillna("")
        df["cast"] = df["cast"].fillna("")
        df["keywords"] = df["keywords"].fillna("")
        df["overview"] = df["overview"].fillna("")
        df["avg_rating"] = df["avg_rating"].fillna(df["avg_rating"].mean())
        df["year"] = df["year"].fillna(df["year"].median()).astype(int)

        if "poster_url" not in df.columns:
            df["poster_url"] = ""

        # Fill any missing poster_url with curated poster
        def fix_poster(row):
            p = str(row.get("poster_url", ""))
            if not p or p == "nan" or "unsplash" in p or len(p) < 10:
                return CURATED_POSTERS.get(int(row["movie_id"]), "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg")
            return p

        df["poster_url"] = df.apply(fix_poster, axis=1)
        return df

    def _clean_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in ["title", "genre", "director", "cast", "keywords", "overview"]:
            df[col] = df[col].astype(str).apply(self._clean_str)
        return df

    @staticmethod
    def _clean_str(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _normalize_ratings(df: pd.DataFrame) -> pd.DataFrame:
        if "avg_rating" in df.columns:
            df["avg_rating"] = df["avg_rating"].clip(0, 10)
        return df

    @staticmethod
    def _build_soup(df: pd.DataFrame) -> pd.DataFrame:
        """Concatenate text columns into a single 'soup' for TF-IDF."""
        def make_soup(row):
            parts = [
                row.get("genre", ""),
                row.get("director", ""),
                row.get("cast", ""),
                row.get("keywords", ""),
                row.get("overview", ""),
            ]
            return " ".join(str(p) for p in parts if p)

        df["soup"] = df.apply(make_soup, axis=1)
        return df
