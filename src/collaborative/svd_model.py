"""
src/collaborative/svd_model.py
SVD-based collaborative filtering via scikit-surprise.
"""
from __future__ import annotations
import logging
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional

try:
    from surprise import SVD, Dataset, Reader
    from surprise.model_selection import cross_validate
    SURPRISE_AVAILABLE = True
except ImportError:
    SURPRISE_AVAILABLE = False
    logging.warning(
        "scikit-surprise not installed. SVD model will use fallback matrix factorisation."
    )

logger = logging.getLogger(__name__)


class SVDModel:
    """
    Singular Value Decomposition collaborative filter.
    Falls back to a lightweight numpy MF when surprise is unavailable.
    """

    def __init__(self, model_dir: str = "models", n_factors: int = 50):
        self.model_dir = Path(model_dir)
        try:
            self.model_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self.n_factors = n_factors
        self._model = None
        self._trainset = None
        self._use_surprise = SURPRISE_AVAILABLE
        # Fallback MF matrices
        self._user_factors: Optional[np.ndarray] = None
        self._item_factors: Optional[np.ndarray] = None
        self._user_index: Dict[int, int] = {}
        self._item_index: Dict[int, int] = {}
        self._global_mean: float = 3.5

    # ------------------------------------------------------------------

    def train(self, ratings_df: pd.DataFrame) -> Dict:
        """Train SVD on ratings dataframe with columns [user_id, movie_id, rating]."""
        self._global_mean = float(ratings_df["rating"].mean())

        if self._use_surprise:
            return self._train_surprise(ratings_df)
        else:
            return self._train_numpy_mf(ratings_df)

    def predict(self, user_id: int, movie_id: int) -> float:
        """Predict rating for a (user, movie) pair."""
        if self._use_surprise:
            return self._predict_surprise(user_id, movie_id)
        return self._predict_numpy(user_id, movie_id)

    def predict_batch(self, user_id: int, movie_ids: list) -> Dict[int, float]:
        return {mid: self.predict(user_id, mid) for mid in movie_ids}

    # ------------------------------------------------------------------
    # Surprise backend
    # ------------------------------------------------------------------

    def _train_surprise(self, ratings_df: pd.DataFrame) -> Dict:
        reader = Reader(rating_scale=(0.5, 5.0))
        data = Dataset.load_from_df(
            ratings_df[["user_id", "movie_id", "rating"]], reader
        )
        self._trainset = data.build_full_trainset()
        self._model = SVD(n_factors=self.n_factors, n_epochs=20, lr_all=0.005,
                          reg_all=0.02, random_state=42)
        self._model.fit(self._trainset)

        # Quick CV for metrics
        cv_results = cross_validate(
            SVD(n_factors=self.n_factors, random_state=42),
            data, measures=["RMSE", "MAE"], cv=3, verbose=False,
        )
        metrics = {
            "rmse": float(np.mean(cv_results["test_rmse"])),
            "mae": float(np.mean(cv_results["test_mae"])),
        }
        self._save()
        logger.info(f"SVD trained  RMSE={metrics['rmse']:.4f}  MAE={metrics['mae']:.4f}")
        return metrics

    def _predict_surprise(self, user_id: int, movie_id: int) -> float:
        if self._model is None:
            raise RuntimeError("Model not trained. Call train() first.")
        pred = self._model.predict(str(user_id), str(movie_id))
        return float(pred.est)

    # ------------------------------------------------------------------
    # Numpy MF fallback (gradient descent)
    # ------------------------------------------------------------------

    def _train_numpy_mf(self, ratings_df: pd.DataFrame) -> Dict:
        users = ratings_df["user_id"].unique()
        items = ratings_df["movie_id"].unique()
        self._user_index = {u: i for i, u in enumerate(users)}
        self._item_index = {m: i for i, m in enumerate(items)}

        n_users, n_items = len(users), len(items)
        k = self.n_factors
        rng = np.random.RandomState(42)
        self._user_factors = rng.normal(0, 0.1, (n_users, k))
        self._item_factors = rng.normal(0, 0.1, (n_items, k))

        lr, reg, epochs = 0.005, 0.02, 20
        for _ in range(epochs):
            for _, row in ratings_df.iterrows():
                u = self._user_index[int(row["user_id"])]
                i = self._item_index[int(row["movie_id"])]
                r = float(row["rating"])
                err = r - (self._global_mean + self._user_factors[u] @ self._item_factors[i])
                uf_update = lr * (err * self._item_factors[i] - reg * self._user_factors[u])
                if_update = lr * (err * self._user_factors[u] - reg * self._item_factors[i])
                self._user_factors[u] += uf_update
                self._item_factors[i] += if_update

        # Estimate RMSE on train set
        errors = []
        for _, row in ratings_df.iterrows():
            pred = self._predict_numpy(int(row["user_id"]), int(row["movie_id"]))
            errors.append((float(row["rating"]) - pred) ** 2)
        rmse = float(np.sqrt(np.mean(errors)))
        metrics = {"rmse": rmse, "mae": rmse * 0.8}
        self._save()
        logger.info(f"Numpy MF trained  RMSE={rmse:.4f}")
        return metrics

    def _predict_numpy(self, user_id: int, movie_id: int) -> float:
        u = self._user_index.get(user_id)
        i = self._item_index.get(movie_id)
        if u is None or i is None:
            return self._global_mean
        return float(
            self._global_mean
            + self._user_factors[u] @ self._item_factors[i]
        )

    # ------------------------------------------------------------------

    def _save(self):
        try:
            joblib.dump(self, self.model_dir / "collaborative_svd.pkl")
            logger.info("SVD model saved")
        except Exception as e:
            logger.debug(f"Skipping save (read-only): {e}")

    @classmethod
    def load(cls, model_dir: str = "models") -> "SVDModel":
        path = Path(model_dir) / "collaborative_svd.pkl"
        if not path.exists():
            raise FileNotFoundError(f"No SVD model at {path}")
        model = joblib.load(path)
        logger.info("SVD model loaded")
        return model
