"""
src/content_based/tfidf.py
TF-IDF vectorisation of movie metadata.
"""
from __future__ import annotations
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer as SklearnTFIDF
from scipy.sparse import csr_matrix

logger = logging.getLogger(__name__)


class TFIDFVectorizer:
    """Wraps sklearn TfidfVectorizer for movie metadata."""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        try:
            self.model_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._vectorizer = SklearnTFIDF(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
            min_df=1,
            sublinear_tf=True,
        )
        self.tfidf_matrix: Optional[csr_matrix] = None
        self.movie_indices: Optional[pd.Series] = None

    # ------------------------------------------------------------------

    def fit_transform(self, movies_df: pd.DataFrame) -> csr_matrix:
        """Fit on 'soup' column and return TF-IDF matrix."""
        soups = movies_df["soup"].fillna("").tolist()
        self.tfidf_matrix = self._vectorizer.fit_transform(soups)
        self.movie_indices = pd.Series(
            movies_df.index, index=movies_df["title"]
        )
        logger.info(
            f"TF-IDF matrix shape: {self.tfidf_matrix.shape}"
        )
        self._save()
        return self.tfidf_matrix

    def transform(self, texts: List[str]) -> csr_matrix:
        """Transform new texts using the fitted vectorizer."""
        return self._vectorizer.transform(texts)

    def get_feature_names(self) -> List[str]:
        return self._vectorizer.get_feature_names_out().tolist()

    # ------------------------------------------------------------------

    def _save(self):
        try:
            joblib.dump(
                self._vectorizer,
                self.model_dir / "tfidf_vectorizer.pkl",
            )
            logger.info("TF-IDF vectorizer saved")
        except Exception as e:
            logger.debug(f"Skipping save (read-only): {e}")

    def load(self):
        path = self.model_dir / "tfidf_vectorizer.pkl"
        if not path.exists():
            raise FileNotFoundError(f"No vectorizer at {path}")
        self._vectorizer = joblib.load(path)
        logger.info("TF-IDF vectorizer loaded")
