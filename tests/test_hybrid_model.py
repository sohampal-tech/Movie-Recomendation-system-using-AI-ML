"""
tests/test_hybrid_model.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.data.load_data import DataLoader
from src.data.preprocess import DataPreprocessor
from src.content_based.tfidf import TFIDFVectorizer
from src.content_based.similarity import SimilarityCalculator
from src.collaborative.svd_model import SVDModel
from src.collaborative.predictions import CollaborativePredictions
from src.hybrid.hybrid_recommender import HybridRecommender
from src.evaluation.metrics import RecommenderMetrics


class TestHybridRecommender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loader = DataLoader(data_dir="data")
        pp = DataPreprocessor(processed_dir="data/processed")
        movies_raw = loader._generate_movies()
        cls.movies  = pp.preprocess_movies(movies_raw)
        cls.ratings = pp.preprocess_ratings(loader._generate_ratings())

        tfidf = TFIDFVectorizer(model_dir="models")
        matrix = tfidf.fit_transform(cls.movies)
        sim = SimilarityCalculator(model_dir="models")
        sim.fit(matrix, cls.movies)

        svd = SVDModel(model_dir="models", n_factors=20)
        svd.train(cls.ratings)
        cf = CollaborativePredictions(svd, cls.ratings)

        cls.hybrid = HybridRecommender(cf, sim, cls.movies, alpha=0.6, top_k=10)

    def test_recommend_returns_list(self):
        uid = int(self.ratings["user_id"].iloc[0])
        recs = self.hybrid.recommend(uid)
        self.assertIsInstance(recs, list)
        self.assertLessEqual(len(recs), 10)

    def test_recommend_sorted_by_hybrid_score(self):
        uid = int(self.ratings["user_id"].iloc[0])
        recs = self.hybrid.recommend(uid)
        scores = [r["hybrid_score"] for r in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_recommend_fields(self):
        uid = int(self.ratings["user_id"].iloc[0])
        recs = self.hybrid.recommend(uid)
        if recs:
            rec = recs[0]
            for field in ["movie_id","title","hybrid_score","collaborative_score","content_score"]:
                self.assertIn(field, rec)

    def test_recommend_by_movie(self):
        mid = int(self.movies.iloc[0]["movie_id"])
        similar = self.hybrid.recommend_by_movie(mid, top_k=5)
        self.assertIsInstance(similar, list)
        ids = [s["movie_id"] for s in similar]
        self.assertNotIn(mid, ids)

    def test_alpha_update(self):
        self.hybrid.update_alpha(0.3)
        self.assertAlmostEqual(self.hybrid.alpha, 0.3)
        self.hybrid.update_alpha(0.6)

    def test_evaluation_metrics(self):
        evaluator = RecommenderMetrics()
        metrics = evaluator.evaluate_recommender(self.hybrid, self.ratings, k=5, n_users=10)
        self.assertIn("precision@5", metrics)
        self.assertIn("recall@5",    metrics)
        self.assertIn("ndcg@5",      metrics)


if __name__ == "__main__":
    unittest.main()
