"""
tests/test_preprocessing.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import pandas as pd
from src.data.load_data import DataLoader
from src.data.preprocess import DataPreprocessor


class TestDataLoader(unittest.TestCase):
    def test_generate_movies(self):
        loader = DataLoader(data_dir="data")
        movies = loader._generate_movies()
        self.assertGreaterEqual(len(movies), 50)
        self.assertIn("movie_id", movies.columns)
        self.assertIn("title",    movies.columns)
        self.assertIn("genre",    movies.columns)

    def test_generate_ratings(self):
        loader = DataLoader(data_dir="data")
        ratings = loader._generate_ratings()
        self.assertGreater(len(ratings), 1000)
        self.assertIn("user_id",  ratings.columns)
        self.assertIn("movie_id", ratings.columns)
        self.assertIn("rating",   ratings.columns)
        self.assertTrue((ratings["rating"] >= 0.5).all())
        self.assertTrue((ratings["rating"] <= 5.0).all())


class TestDataPreprocessor(unittest.TestCase):
    def setUp(self):
        loader = DataLoader(data_dir="data")
        self.movies  = loader._generate_movies()
        self.ratings = loader._generate_ratings()
        self.pp = DataPreprocessor(processed_dir="data/processed")

    def test_preprocess_movies_no_nan(self):
        clean = self.pp.preprocess_movies(self.movies)
        self.assertFalse(clean["title"].isna().any())
        self.assertFalse(clean["genre"].isna().any())
        self.assertIn("soup", clean.columns)

    def test_preprocess_ratings_no_dups(self):
        clean = self.pp.preprocess_ratings(self.ratings)
        dups = clean.duplicated(subset=["user_id","movie_id"]).sum()
        self.assertEqual(dups, 0)

    def test_feature_matrix_shape(self):
        clean = self.pp.preprocess_movies(self.movies)
        feats = self.pp.build_movie_features(clean)
        self.assertEqual(len(feats), len(clean))


if __name__ == "__main__":
    unittest.main()
