"""
src/content_based/similarity.py
Cosine similarity computation and content-based score retrieval.
"""
from __future__ import annotations
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix

logger = logging.getLogger(__name__)


class SimilarityCalculator:
    """Computes and persists the cosine similarity matrix."""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.similarity_matrix: Optional[np.ndarray] = None
        self.movies_df: Optional[pd.DataFrame] = None

    # ------------------------------------------------------------------

    def fit(self, tfidf_matrix: csr_matrix, movies_df: pd.DataFrame) -> "SimilarityCalculator":
        """Compute and save the full cosine similarity matrix."""
        logger.info("Computing cosine similarity matrix…")
        self.similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        self.movies_df = movies_df.reset_index(drop=True)
        self._save()
        logger.info(f"Similarity matrix shape: {self.similarity_matrix.shape}")
        return self

    def get_similar_movies(
        self,
        movie_id: int,
        top_k: int = 10,
        exclude_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        """Return top-k most similar movies for a given movie_id."""
        if self.similarity_matrix is None or self.movies_df is None:
            raise RuntimeError("Call fit() or load() first")

        idx_series = self.movies_df[self.movies_df["movie_id"] == movie_id].index
        if idx_series.empty:
            logger.warning(f"movie_id {movie_id} not found")
            return []

        idx = idx_series[0]
        scores = list(enumerate(self.similarity_matrix[idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        exclude_ids_set = set(exclude_ids or [])
        exclude_ids_set.add(movie_id)

        results = []
        for i, score in scores:
            row = self.movies_df.iloc[i]
            mid = int(row["movie_id"])
            if mid in exclude_ids_set:
                continue
            results.append({
                "movie_id": mid,
                "title": row["title"],
                "genre": row.get("genre", ""),
                "content_score": float(score),
            })
            if len(results) >= top_k:
                break
        return results

    def score_for_user(
        self,
        liked_movie_ids: List[int],
        candidate_movie_ids: List[int],
    ) -> Dict[int, float]:
        """
        Average content similarity between candidate movies and liked movies.
        Returns {movie_id: avg_cosine_score}.
        """
        if self.similarity_matrix is None or self.movies_df is None:
            raise RuntimeError("Call fit() or load() first")

        movie_id_to_idx = dict(
            zip(self.movies_df["movie_id"].tolist(), self.movies_df.index.tolist())
        )
        liked_indices = [
            movie_id_to_idx[m] for m in liked_movie_ids if m in movie_id_to_idx
        ]
        scores: Dict[int, float] = {}
        for cand_id in candidate_movie_ids:
            if cand_id not in movie_id_to_idx:
                scores[cand_id] = 0.0
                continue
            cand_idx = movie_id_to_idx[cand_id]
            if liked_indices:
                avg = float(
                    np.mean([self.similarity_matrix[cand_idx][li] for li in liked_indices])
                )
            else:
                avg = 0.0
            scores[cand_id] = avg
        return scores

    # ------------------------------------------------------------------

    def _save(self):
        joblib.dump(
            self.similarity_matrix,
            self.model_dir / "similarity_matrix.pkl",
        )
        logger.info("Similarity matrix saved")

    def load(self, movies_df: pd.DataFrame):
        path = self.model_dir / "similarity_matrix.pkl"
        if not path.exists():
            raise FileNotFoundError(f"No similarity matrix at {path}")
        self.similarity_matrix = joblib.load(path)
        self.movies_df = movies_df.reset_index(drop=True)
        logger.info(f"Similarity matrix loaded: {self.similarity_matrix.shape}")
