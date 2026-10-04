"""
src/evaluation/metrics.py
RMSE, MAE, Precision@K, Recall@K, NDCG@K for the recommender.
"""
from __future__ import annotations
import logging
from typing import Dict, List, Set
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RecommenderMetrics:
    """Evaluation metrics for rating prediction and ranking quality."""

    # ------------------------------------------------------------------
    # Rating prediction metrics
    # ------------------------------------------------------------------

    @staticmethod
    def rmse(y_true: List[float], y_pred: List[float]) -> float:
        """Root Mean Squared Error."""
        arr_true = np.array(y_true, dtype=float)
        arr_pred = np.array(y_pred, dtype=float)
        return float(np.sqrt(np.mean((arr_true - arr_pred) ** 2)))

    @staticmethod
    def mae(y_true: List[float], y_pred: List[float]) -> float:
        """Mean Absolute Error."""
        arr_true = np.array(y_true, dtype=float)
        arr_pred = np.array(y_pred, dtype=float)
        return float(np.mean(np.abs(arr_true - arr_pred)))

    # ------------------------------------------------------------------
    # Ranking metrics
    # ------------------------------------------------------------------

    @staticmethod
    def precision_at_k(
        recommended: List[int],
        relevant: Set[int],
        k: int,
    ) -> float:
        """Fraction of top-k recommended items that are relevant."""
        top_k = recommended[:k]
        hits = sum(1 for m in top_k if m in relevant)
        return hits / k if k > 0 else 0.0

    @staticmethod
    def recall_at_k(
        recommended: List[int],
        relevant: Set[int],
        k: int,
    ) -> float:
        """Fraction of relevant items that appear in top-k."""
        top_k = recommended[:k]
        if not relevant:
            return 0.0
        hits = sum(1 for m in top_k if m in relevant)
        return hits / len(relevant)

    @staticmethod
    def ndcg_at_k(
        recommended: List[int],
        relevant: Set[int],
        k: int,
    ) -> float:
        """Normalised Discounted Cumulative Gain at K."""
        top_k = recommended[:k]
        dcg = sum(
            1.0 / np.log2(rank + 2)
            for rank, item in enumerate(top_k)
            if item in relevant
        )
        ideal_hits = min(len(relevant), k)
        idcg = sum(1.0 / np.log2(rank + 2) for rank in range(ideal_hits))
        return float(dcg / idcg) if idcg > 0 else 0.0

    # ------------------------------------------------------------------
    # Batch evaluation
    # ------------------------------------------------------------------

    def evaluate_recommender(
        self,
        recommender,
        ratings_df: pd.DataFrame,
        k: int = 10,
        n_users: int = 50,
        threshold: float = 4.0,
    ) -> Dict:
        """
        Evaluate on a random sample of users.
        Uses leave-last-out: the most recent rating per user is the test item.
        """
        logger.info(f"Evaluating on {n_users} users (K={k})")
        ratings_df = ratings_df.sort_values("timestamp", ascending=False)
        user_ids = ratings_df["user_id"].unique()
        sampled = np.random.choice(user_ids, min(n_users, len(user_ids)), replace=False)

        p_scores: List[float] = []
        r_scores: List[float] = []
        ndcg_scores: List[float] = []

        for uid in sampled:
            user_ratings = ratings_df[ratings_df["user_id"] == uid]
            if len(user_ratings) < 3:
                continue
            # Hold out last-rated movie
            test_movie = int(user_ratings.iloc[0]["movie_id"])
            # Relevant = movies with rating >= threshold
            relevant: Set[int] = set(
                user_ratings[user_ratings["rating"] >= threshold]["movie_id"].astype(int)
            )
            relevant.discard(test_movie)
            relevant.add(test_movie)

            try:
                recs = recommender.recommend(int(uid), exclude_watched=False)
                rec_ids = [r["movie_id"] for r in recs]
            except Exception:
                continue

            p_scores.append(self.precision_at_k(rec_ids, relevant, k))
            r_scores.append(self.recall_at_k(rec_ids, relevant, k))
            ndcg_scores.append(self.ndcg_at_k(rec_ids, relevant, k))

        return {
            f"precision@{k}": round(float(np.mean(p_scores)), 4) if p_scores else 0.0,
            f"recall@{k}": round(float(np.mean(r_scores)), 4) if r_scores else 0.0,
            f"ndcg@{k}": round(float(np.mean(ndcg_scores)), 4) if ndcg_scores else 0.0,
            "n_users_evaluated": len(p_scores),
        }
