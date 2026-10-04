"""
tests/test_content_model.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from src.data.load_data import DataLoader
from src.data.preprocess import DataPreprocessor
from src.content_based.tfidf import TFIDFVectorizer
from src.content_based.similarity import SimilarityCalculator


class TestContentModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loader = DataLoader(data_dir="data")
        pp = DataPreprocessor(processed_dir="data/processed")
        movies_raw = loader._generate_movies()
        cls.movies = pp.preprocess_movies(movies_raw)

        tfidf = TFIDFVectorizer(model_dir="models")
        matrix = tfidf.fit_transform(cls.movies)

        cls.sim = SimilarityCalculator(model_dir="models")
        cls.sim.fit(matrix, cls.movies)

    def test_tfidf_matrix_shape(self):
        self.assertEqual(self.sim.similarity_matrix.shape[0], len(self.movies))
        self.assertEqual(self.sim.similarity_matrix.shape[1], len(self.movies))

    def test_similarity_diagonal_is_one(self):
        import numpy as np
        diag = self.sim.similarity_matrix.diagonal()
        self.assertTrue(all(abs(d - 1.0) < 1e-6 for d in diag))

    def test_similar_movies_returns_list(self):
        mid = int(self.movies.iloc[0]["movie_id"])
        similar = self.sim.get_similar_movies(mid, top_k=5)
        self.assertIsInstance(similar, list)
        self.assertLessEqual(len(similar), 5)
        # Should not include the queried movie
        ids = [s["movie_id"] for s in similar]
        self.assertNotIn(mid, ids)

    def test_score_for_user(self):
        liked = [1, 2, 3]
        candidates = [4, 5, 6, 7]
        scores = self.sim.score_for_user(liked, candidates)
        self.assertEqual(set(scores.keys()), set(candidates))
        for v in scores.values():
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)


if __name__ == "__main__":
    unittest.main()
