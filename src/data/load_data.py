"""
src/data/load_data.py
Handles loading raw CSVs and generating 200 iconic real movies with authentic TMDB poster URLs.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from src.data.populate_real_movies import ALL_200_MOVIES, build_complete_catalogue

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads raw data from CSV files or generates 200 authentic real movies."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"

    def load_movies(self) -> pd.DataFrame:
        path = self.raw_dir / "movies.csv"
        if path.exists():
            df = pd.read_csv(path)
            # Ensure it has poster_url and not generic synthetic titles
            if "poster_url" in df.columns and len(df) >= 200 and "Movie Title" not in str(df.iloc[60]["title"]):
                logger.info(f"Loaded {len(df)} authentic movies from {path}")
                return df

        logger.info("Generating full 200 real movie catalogue...")
        return self._generate_movies()

    def load_ratings(self) -> pd.DataFrame:
        path = self.raw_dir / "ratings.csv"
        if path.exists():
            df = pd.read_csv(path)
            logger.info(f"Loaded {len(df)} ratings from {path}")
            return df
        logger.info("ratings.csv not found – generating sample ratings")
        return self._generate_ratings()

    def load_credits(self) -> pd.DataFrame:
        path = self.raw_dir / "credits.csv"
        if path.exists():
            df = pd.read_csv(path)
            logger.info(f"Loaded {len(df)} credits from {path}")
            return df
        return pd.DataFrame(columns=["movie_id", "cast", "crew"])

    def _generate_movies(self) -> pd.DataFrame:
        from src.data.populate_real_movies import build_complete_catalogue
        build_complete_catalogue()
        return pd.read_csv(self.raw_dir / "movies.csv")

    def _generate_ratings(self) -> pd.DataFrame:
        np.random.seed(42)
        n_users, n_movies, n_ratings = 500, 200, 15000
        user_ids = np.random.randint(1, n_users + 1, n_ratings)
        movie_ids = np.random.randint(1, n_movies + 1, n_ratings)
        pairs = list(set(zip(user_ids.tolist(), movie_ids.tolist())))
        np.random.shuffle(pairs)
        pairs = pairs[:n_ratings]
        ratings = np.clip(
            np.round(np.random.normal(3.8, 1.1, len(pairs)) * 2) / 2, 0.5, 5.0
        )
        timestamps = np.random.randint(1_000_000_000, 1_700_000_000, len(pairs))
        df = pd.DataFrame({
            "user_id": [p[0] for p in pairs],
            "movie_id": [p[1] for p in pairs],
            "rating": ratings,
            "timestamp": timestamps,
        })
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.raw_dir / "ratings.csv", index=False)
        return df
