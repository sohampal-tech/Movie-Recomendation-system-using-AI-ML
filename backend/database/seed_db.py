"""
backend/database/seed_db.py
Seeds movies, sample users, and ratings into the database (Neon PostgreSQL or SQLite).
"""
import os
import logging
import pandas as pd
from backend.database.connection import SessionLocal
from backend.database.models import Base, User, Movie, Rating, init_db
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

def seed_database_if_empty(force_reload_movies: bool = True):
    """Initializes tables and populates movies & sample users."""
    init_db()
    db = SessionLocal()
    try:
        csv_path = os.path.join("data", "processed", "movies_clean.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join("data", "raw", "movies.csv")

        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            movie_count = db.query(Movie).count()
            
            # If empty or force refresh requested
            if movie_count < len(df) or force_reload_movies:
                logger.info(f"Syncing {len(df)} real movies into database...")
                db.query(Movie).delete()
                db.commit()

                movies_to_insert = []
                for _, row in df.iterrows():
                    m = Movie(
                        movie_id=int(row["movie_id"]),
                        title=str(row.get("title", "")),
                        year=int(row["year"]) if pd.notna(row.get("year")) else None,
                        genre=str(row.get("genre", "")),
                        director=str(row.get("director", "")),
                        cast=str(row.get("cast", "")),
                        overview=str(row.get("overview", "")),
                        language=str(row.get("language", "English")),
                        avg_rating=float(row.get("avg_rating", 0.0)) if pd.notna(row.get("avg_rating")) else 0.0,
                    )
                    movies_to_insert.append(m)
                
                db.bulk_save_objects(movies_to_insert)
                db.commit()
                logger.info(f"Synced {len(movies_to_insert)} movies into database.")

        user_count = db.query(User).count()
        if user_count == 0:
            logger.info("Seeding initial demo users...")
            demo_users = [
                User(user_id=1, username="alice", email="alice@cinematch.ai", password_hash=generate_password_hash("password123"), favorite_genres="Action|Sci-Fi"),
                User(user_id=2, username="bob", email="bob@cinematch.ai", password_hash=generate_password_hash("password123"), favorite_genres="Comedy|Romance"),
                User(user_id=3, username="carol", email="carol@cinematch.ai", password_hash=generate_password_hash("password123"), favorite_genres="Drama|Thriller"),
                User(user_id=42, username="demo_user", email="demo@cinematch.ai", password_hash=generate_password_hash("demo1234"), favorite_genres="Action|Adventure|Sci-Fi"),
                User(user_id=100, username="cinephile", email="cinephile@cinematch.ai", password_hash=generate_password_hash("password123"), favorite_genres="All"),
            ]
            db.bulk_save_objects(demo_users)
            db.commit()
            logger.info("Demo users seeded.")
    except Exception as e:
        logger.warning(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database_if_empty(force_reload_movies=True)
