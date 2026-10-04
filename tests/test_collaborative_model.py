"""
tests/test_collaborative_model.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.data.load_data import DataLoader
from src.data.preprocess import DataPreprocessor
from src.collaborative.svd_model import SVDModel
from src.collaborative.predictions import CollaborativePredictions


class TestCollaborativeModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loader = DataLoader(data_dir="data")
        pp = DataPreprocessor(processed_dir="data/processed")
        cls.ratings = pp.preprocess_ratings(loader._generate_ratings())
        cls.svd = SVDModel(model_dir="models", n_factors=20)
        cls.metrics = cls.svd.train(cls.ratings)
        cls.cf = CollaborativePredictions(cls.svd, cls.ratings)

    def test_metrics_present(self):
        self.assertIn("rmse", self.metrics)
        self.assertIn("mae",  self.metrics)
        self.assertLess(self.metrics["rmse"], 5.0)

    def test_predict_returns_float(self):
        user_id  = int(self.ratings["user_id"].iloc[0])
        movie_id = int(self.ratings["movie_id"].iloc[0])
        pred = self.svd.predict(user_id, movie_id)
        self.assertIsInstance(pred, float)

    def test_predict_top_k(self):
        user_id = int(self.ratings["user_id"].iloc[0])
        all_ids = self.ratings["movie_id"].unique().tolist()
        results = self.cf.predict_top_k(user_id, all_ids[:50], top_k=10)
        self.assertLessEqual(len(results), 10)
        scores = [r["collaborative_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_liked_movies(self):
        user_id = int(self.ratings["user_id"].iloc[0])
        liked = self.cf.get_liked_movies(user_id, threshold=3.5)
        self.assertIsInstance(liked, list)


if __name__ == "__main__":
    unittest.main()
