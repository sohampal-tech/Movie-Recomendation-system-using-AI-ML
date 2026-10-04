"""
src/hybrid/hybrid_recommender.py
Combines collaborative + content-based scores with weighted blending.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from src.content_based.similarity import SimilarityCalculator
from src.collaborative.predictions import CollaborativePredictions
from src.utils.helpers import normalize_scores
from src.data.fetch_posters import CURATED_POSTERS

logger = logging.getLogger(__name__)


class HybridRecommender:
    """
    Hybrid recommender combining Collaborative Filtering (SVD) and
    Content-Based Filtering (TF-IDF + Cosine Similarity).

    Formula:
        HybridScore = alpha * CF_score + (1 - alpha) * CB_score
    """

    def __init__(
        self,
        collaborative_predictions: CollaborativePredictions,
        similarity_calculator: SimilarityCalculator,
        movies_df: pd.DataFrame,
        alpha: float = 0.6,
        top_k: int = 10,
    ):
        self.cf = collaborative_predictions
        self.cb = similarity_calculator
        self.movies_df = movies_df
        self.alpha = float(alpha)
        self.top_k = int(top_k)
        self._all_movie_ids = movies_df["movie_id"].tolist()

    def update_alpha(self, new_alpha: float):
        """Dynamically adjust blending weight."""
        if not (0.0 <= new_alpha <= 1.0):
            raise ValueError("alpha must be in [0.0, 1.0]")
        self.alpha = new_alpha
        logger.info(f"Updated alpha to {self.alpha}")

    def recommend(
        self,
        user_id: int,
        top_k: Optional[int] = None,
        exclude_watched: bool = True,
        alpha: Optional[float] = None,
    ) -> List[Dict]:
        """
        Generate top-K hybrid recommendations for user_id.

        Returns list of dicts sorted by hybrid_score desc.
        """
        alpha = alpha if alpha is not None else self.alpha

        # 1. Collaborative scores for all unseen movies
        cf_results = self.cf.predict_top_k(
            user_id, self._all_movie_ids,
            top_k=len(self._all_movie_ids),
            exclude_watched=exclude_watched,
        )
        cf_map: Dict[int, float] = {
            r["movie_id"]: r["collaborative_score"] for r in cf_results
        }

        # 2. Content scores based on liked movies
        liked = self.cf.get_liked_movies(user_id)
        candidate_ids = list(cf_map.keys())
        cb_map: Dict[int, float] = self.cb.score_for_user(liked, candidate_ids)

        # 3. Normalise both score sets to [0, 1]
        cf_norm = normalize_scores(cf_map)
        cb_norm = normalize_scores(cb_map)

        # 4. Compute hybrid scores
        results = []
        movie_lookup = {
            int(row["movie_id"]): row
            for _, row in self.movies_df.iterrows()
        }
        for mid in candidate_ids:
            cs = alpha * cf_norm.get(mid, 0.0) + (1 - alpha) * cb_norm.get(mid, 0.0)
            movie = movie_lookup.get(mid, {})
            poster = str(movie.get("poster_url", "")) if pd.notna(movie.get("poster_url")) else ""
            if not poster or "unsplash" in poster or len(poster) < 10:
                poster = CURATED_POSTERS.get(mid, "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg")

            results.append({
                "movie_id": mid,
                "title": movie.get("title", "Unknown"),
                "genre": movie.get("genre", ""),
                "director": movie.get("director", ""),
                "cast": movie.get("cast", ""),
                "year": int(movie.get("year", 0)) if pd.notna(movie.get("year")) else 0,
                "avg_rating": float(movie.get("avg_rating", 0)) if pd.notna(movie.get("avg_rating")) else 0.0,
                "overview": movie.get("overview", ""),
                "poster_url": poster,
                "hybrid_score": round(cs, 4),
                "collaborative_score": round(cf_norm.get(mid, 0.0), 4),
                "content_score": round(cb_norm.get(mid, 0.0), 4),
            })

        # 5. Sort descending
        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        k = top_k if top_k is not None else self.top_k
        return results[:k]

    def recommend_by_movie(self, movie_id: int, top_k: int = 8) -> List[Dict]:
        """Content-only recommendations given a seed movie."""
        sim_scores = self.cb.get_similar_movies(movie_id, top_k=top_k)
        movie_lookup = {
            int(row["movie_id"]): row
            for _, row in self.movies_df.iterrows()
        }
        results = []
        for item in sim_scores:
            if isinstance(item, dict):
                mid = int(item["movie_id"])
                sim = float(item.get("content_score", 0.0))
            elif isinstance(item, (list, tuple)):
                mid = int(item[0])
                sim = float(item[1])
            else:
                continue

            movie = movie_lookup.get(mid, {})
            poster = str(movie.get("poster_url", "")) if pd.notna(movie.get("poster_url")) else ""
            if not poster or "unsplash" in poster or len(poster) < 10:
                poster = CURATED_POSTERS.get(mid, "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg")

            results.append({
                "movie_id": mid,
                "title": movie.get("title", "Unknown"),
                "genre": movie.get("genre", ""),
                "director": movie.get("director", ""),
                "cast": movie.get("cast", ""),
                "year": int(movie.get("year", 0)) if pd.notna(movie.get("year")) else 0,
                "avg_rating": float(movie.get("avg_rating", 0)) if pd.notna(movie.get("avg_rating")) else 0.0,
                "poster_url": poster,
                "similarity_score": round(sim, 4),
            })
        return results
