"""
src/collaborative/predictions.py
Higher-level wrapper to get top-K collaborative predictions for a user.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Set
import numpy as np
import pandas as pd
from .svd_model import SVDModel

logger = logging.getLogger(__name__)


class CollaborativePredictions:
    """Uses a trained SVDModel to rank unseen movies for a user."""

    def __init__(self, svd_model: SVDModel, ratings_df: pd.DataFrame):
        self.svd = svd_model
        self.ratings_df = ratings_df

    def get_watched_movies(self, user_id: int) -> Set[int]:
        watched = self.ratings_df[
            self.ratings_df["user_id"] == user_id
        ]["movie_id"].tolist()
        return set(int(m) for m in watched)

    def predict_top_k(
        self,
        user_id: int,
        all_movie_ids: List[int],
        top_k: int = 20,
        exclude_watched: bool = True,
    ) -> List[Dict]:
        """
        Returns list of dicts: {movie_id, collaborative_score}
        sorted descending by collaborative_score.
        """
        watched = self.get_watched_movies(user_id) if exclude_watched else set()
        candidates = [m for m in all_movie_ids if m not in watched]

        scores = []
        for mid in candidates:
            score = self.svd.predict(user_id, mid)
            scores.append({"movie_id": mid, "collaborative_score": score})

        scores.sort(key=lambda x: x["collaborative_score"], reverse=True)
        return scores[:top_k]

    def get_liked_movies(self, user_id: int, threshold: float = 3.5) -> List[int]:
        """Return movies rated at or above threshold by the user."""
        liked = self.ratings_df[
            (self.ratings_df["user_id"] == user_id)
            & (self.ratings_df["rating"] >= threshold)
        ]["movie_id"].tolist()
        return [int(m) for m in liked]
