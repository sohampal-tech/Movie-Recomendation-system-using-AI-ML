"""
backend/database/queries.py
Common database queries.
"""
from sqlalchemy.orm import Session


def get_all_movies(db: Session, skip: int = 0, limit: int = 20):
    from sqlalchemy import text
    result = db.execute(
        text("SELECT * FROM movies ORDER BY avg_rating DESC LIMIT :limit OFFSET :skip"),
        {"limit": limit, "skip": skip},
    )
    return result.fetchall()


def get_user_ratings(db: Session, user_id: int):
    from sqlalchemy import text
    result = db.execute(
        text("SELECT * FROM ratings WHERE user_id = :uid ORDER BY timestamp DESC"),
        {"uid": user_id},
    )
    return result.fetchall()
