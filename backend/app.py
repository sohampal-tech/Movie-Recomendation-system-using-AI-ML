"""
backend/app.py
Flask application factory, database initialization, and model bootstrap.
"""
import os
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from src.utils.helpers import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

from src.data.load_data import DataLoader
from src.data.preprocess import DataPreprocessor
from src.content_based.tfidf import TFIDFVectorizer
from src.content_based.similarity import SimilarityCalculator
from src.collaborative.svd_model import SVDModel
from src.collaborative.predictions import CollaborativePredictions
from src.hybrid.hybrid_recommender import HybridRecommender
from src.evaluation.metrics import RecommenderMetrics
from backend.database.seed_db import seed_database_if_empty


def bootstrap_models(app: Flask):
    """Train or load all ML models and attach to app."""
    # Ensure database tables exist and are seeded
    try:
        seed_database_if_empty()
    except Exception as e:
        logger.warning(f"Database bootstrap warning: {e}")

    model_dir = "models"
    try:
        Path(model_dir).mkdir(exist_ok=True)
    except Exception:
        pass

    loader = DataLoader()
    preprocessor = DataPreprocessor()

    # Load from processed cache for instant serverless cold-start
    proc_movies = Path("data/processed/movies_clean.csv")
    proc_ratings = Path("data/processed/ratings_clean.csv")

    if proc_movies.exists():
        movies = pd.read_csv(proc_movies)
    else:
        movies_raw = loader.load_movies()
        movies = preprocessor.preprocess_movies(movies_raw)

    if proc_ratings.exists():
        ratings = pd.read_csv(proc_ratings)
    else:
        ratings_raw = loader.load_ratings()
        ratings = preprocessor.preprocess_ratings(ratings_raw)

    try:
        preprocessor.build_movie_features(movies)
    except Exception:
        pass

    # Content-based
    tfidf = TFIDFVectorizer(model_dir=model_dir)
    sim_calc = SimilarityCalculator(model_dir=model_dir)

    try:
        tfidf.load()
        sim_calc.load(movies)
        logger.info("Loaded existing content-based models")
    except Exception:
        logger.info("Training content-based models…")
        tfidf_matrix = tfidf.fit_transform(movies)
        sim_calc.fit(tfidf_matrix, movies)

    # Collaborative
    try:
        svd = SVDModel.load(model_dir=model_dir)
        logger.info("Loaded existing SVD model")
    except Exception:
        logger.info("Training SVD model…")
        svd = SVDModel(model_dir=model_dir)
        metrics = svd.train(ratings)
        logger.info(f"SVD metrics: {metrics}")

    cf_preds = CollaborativePredictions(svd, ratings)

    alpha = float(os.getenv("ALPHA", 0.6))
    top_k = int(os.getenv("TOP_K", 10))

    hybrid = HybridRecommender(cf_preds, sim_calc, movies, alpha=alpha, top_k=top_k)
    evaluator = RecommenderMetrics()

    # Attach to app
    app.config["hybrid"] = hybrid
    app.config["movies_df"] = movies
    app.config["ratings_df"] = ratings
    app.config["evaluator"] = evaluator
    app.config["sim_calc"] = sim_calc
    app.config["cf_preds"] = cf_preds
    logger.info("All models and database connections bootstrapped successfully")


def create_app() -> Flask:
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    app.secret_key = os.getenv("JWT_SECRET", "cinematch-super-secret-key")
    CORS(app)

    # Register blueprints
    from backend.routes.movies import movies_bp
    from backend.routes.recommendations import recs_bp
    from backend.routes.users import users_bp

    app.register_blueprint(movies_bp, url_prefix="/api/movies")
    app.register_blueprint(recs_bp, url_prefix="/api/recommendations")
    app.register_blueprint(users_bp, url_prefix="/api/users")

    # Serve frontend
    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.route("/<path:path>")
    def serve_static(path):
        try:
            return app.send_static_file(path)
        except Exception:
            return app.send_static_file("index.html")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Resource not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(error="Internal server error"), 500

    bootstrap_models(app)
    return app


# Top-level WSGI entry point for Vercel and production servers
app = create_app()
application = app
handler = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
