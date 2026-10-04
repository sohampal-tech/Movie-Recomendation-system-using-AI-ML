"""
backend/routes/users.py
User authentication (JWT, registration, login, logout), profile, watchlist, and ratings.
"""
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import Blueprint, jsonify, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import pandas as pd
from dotenv import load_dotenv

from backend.database.connection import SessionLocal
from backend.database.models import User, Movie, Rating, WatchHistory, Watchlist

load_dotenv()
logger = logging.getLogger(__name__)

users_bp = Blueprint("users", __name__)

JWT_SECRET = os.getenv("JWT_SECRET", "cinematch-secret-key-2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", 1440))  # default 24h


def create_token(user_id: int, username: str, email: Optional[str] = None) -> str:
    """Generate JWT auth token."""
    payload = {
        "user_id": user_id,
        "username": username,
        "email": email or "",
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRY_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT auth token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def get_current_user_id() -> Optional[int]:
    """Extract user_id from Authorization header if present."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if payload and "user_id" in payload:
        return int(payload["user_id"])
    return None


@users_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account with email/username/password."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    favorite_genres = data.get("favorite_genres") or ""

    if not username or not email or not password:
        return jsonify(error="Username, email, and password are required"), 400

    if len(password) < 4:
        return jsonify(error="Password must be at least 4 characters"), 400

    db = SessionLocal()
    try:
        # Check if username or email already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.email == email:
                return jsonify(error="Email is already registered. Please login."), 409
            return jsonify(error="Username is already taken."), 409

        # Generate a unique new user_id (higher than demo range)
        max_id = db.query(User.user_id).order_by(User.user_id.desc()).first()
        next_id = max(501, (max_id[0] + 1) if max_id and max_id[0] else 501)

        new_user = User(
            user_id=next_id,
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            favorite_genres=favorite_genres,
            created_at=datetime.utcnow(),
        )
        db.add(new_user)
        db.commit()

        token = create_token(new_user.user_id, new_user.username, new_user.email)

        return jsonify({
            "message": "Account created successfully! Welcome to CineMatch.",
            "token": token,
            "user": {
                "user_id": new_user.user_id,
                "username": new_user.username,
                "email": new_user.email,
                "favorite_genres": new_user.favorite_genres,
            }
        }), 201

    except Exception as e:
        db.rollback()
        logger.error(f"Register error: {e}")
        return jsonify(error="Registration failed. Please try again."), 500
    finally:
        db.close()


@users_bp.route("/login", methods=["POST"])
def login():
    """Login with credentials (email/username + password) OR Quick User ID."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    email_or_user = (data.get("email") or data.get("username") or "").strip()
    password = data.get("password") or ""

    db = SessionLocal()
    try:
        # Mode 1: Quick User ID mode (for instant demo testing)
        if user_id is not None:
            uid = int(user_id)
            user = db.query(User).filter(User.user_id == uid).first()
            if not user:
                # Auto create demo user
                user = User(
                    user_id=uid,
                    username=f"User #{uid}",
                    email=f"user{uid}@cinematch.ai",
                    favorite_genres="Action|Drama|Sci-Fi",
                )
                db.add(user)
                db.commit()

            token = create_token(user.user_id, user.username or f"User #{uid}", user.email)
            return jsonify({
                "message": f"Signed in as User #{uid}",
                "token": token,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username or f"User #{uid}",
                    "email": user.email or "",
                    "favorite_genres": user.favorite_genres or "",
                },
                "is_new": False,
            })

        # Mode 2: Standard Username/Email + Password
        if not email_or_user or not password:
            return jsonify(error="Please provide email/username and password, or a User ID"), 400

        user = db.query(User).filter(
            (User.email == email_or_user.lower()) | (User.username == email_or_user)
        ).first()

        if not user or not user.password_hash:
            return jsonify(error="Invalid email/username or password"), 401

        if not check_password_hash(user.password_hash, password):
            return jsonify(error="Invalid password. Please check and try again."), 401

        token = create_token(user.user_id, user.username, user.email)
        return jsonify({
            "message": f"Welcome back, {user.username}!",
            "token": token,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "favorite_genres": user.favorite_genres,
            }
        })

    except Exception as e:
        logger.error(f"Login error: {e}")
        # Graceful fallback for demo
        uid = int(user_id) if user_id else 42
        token = create_token(uid, f"User #{uid}")
        return jsonify({
            "message": "Signed in successfully",
            "token": token,
            "user": {"user_id": uid, "username": f"User #{uid}", "email": ""},
        })
    finally:
        db.close()


@users_bp.route("/logout", methods=["POST"])
def logout():
    """Logout endpoint to acknowledge session termination."""
    return jsonify({
        "message": "Logged out successfully. See you again soon!",
        "status": "success"
    })


@users_bp.route("/me", methods=["GET"])
def get_current_user():
    """Get authenticated user info from token."""
    uid = get_current_user_id()
    if not uid:
        return jsonify(error="Not authenticated"), 401

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == uid).first()
        if not user:
            return jsonify({
                "user_id": uid,
                "username": f"User #{uid}",
                "email": "",
                "favorite_genres": "",
            })
        return jsonify({
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "favorite_genres": user.favorite_genres,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    finally:
        db.close()


@users_bp.route("/<int:user_id>/profile", methods=["GET"])
def user_profile(user_id: int):
    ratings_df: pd.DataFrame = current_app.config.get("ratings_df")
    movies_df: pd.DataFrame = current_app.config.get("movies_df")

    db = SessionLocal()
    user_obj = None
    try:
        user_obj = db.query(User).filter(User.user_id == user_id).first()
    except Exception:
        pass
    finally:
        db.close()

    username = user_obj.username if user_obj and user_obj.username else f"User #{user_id}"
    email = user_obj.email if user_obj and user_obj.email else ""
    fav_genres_str = user_obj.favorite_genres if user_obj and user_obj.favorite_genres else ""

    if ratings_df is None or ratings_df.empty:
        return jsonify({
            "user_id": user_id,
            "username": username,
            "email": email,
            "total_ratings": 0,
            "avg_rating_given": 0.0,
            "top_genres": {},
            "recently_rated": [],
        })

    user_ratings = ratings_df[ratings_df["user_id"] == user_id]
    if user_ratings.empty:
        return jsonify({
            "user_id": user_id,
            "username": username,
            "email": email,
            "total_ratings": 0,
            "avg_rating_given": 0.0,
            "top_genres": {g: 1 for g in fav_genres_str.split("|") if g} if fav_genres_str else {},
            "recently_rated": [],
        })

    rated = user_ratings.merge(movies_df, on="movie_id", how="left")
    top_genres = (
        rated["genre"]
        .dropna()
        .str.split("|")
        .explode()
        .value_counts()
        .head(5)
        .to_dict()
    )

    return jsonify({
        "user_id": user_id,
        "username": username,
        "email": email,
        "total_ratings": int(len(user_ratings)),
        "avg_rating_given": round(float(user_ratings["rating"].mean()), 2),
        "top_genres": top_genres,
        "recently_rated": rated.sort_values("timestamp", ascending=False)
            .head(6)[["movie_id", "title", "rating", "genre"]]
            .fillna("")
            .to_dict(orient="records"),
    })


@users_bp.route("/<int:user_id>/history", methods=["GET"])
def watch_history(user_id: int):
    ratings_df: pd.DataFrame = current_app.config.get("ratings_df")
    movies_df: pd.DataFrame = current_app.config.get("movies_df")

    if ratings_df is None:
        return jsonify({"user_id": user_id, "history": []})

    user_ratings = ratings_df[ratings_df["user_id"] == user_id]
    if user_ratings.empty:
        return jsonify({"user_id": user_id, "history": []})

    history = user_ratings.merge(movies_df, on="movie_id", how="left")
    history = history.sort_values("timestamp", ascending=False)
    records = []
    for _, row in history.iterrows():
        records.append({
            "movie_id": int(row["movie_id"]),
            "title": str(row.get("title", "")),
            "genre": str(row.get("genre", "")),
            "rating": float(row["rating"]),
            "year": int(row["year"]) if pd.notna(row.get("year")) else None,
        })
    return jsonify({"user_id": user_id, "history": records})


@users_bp.route("/<int:user_id>/rate", methods=["POST"])
def rate_movie(user_id: int):
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movie_id")
    rating = data.get("rating")

    if movie_id is None or rating is None:
        return jsonify(error="movie_id and rating are required"), 400

    try:
        rating = float(rating)
        movie_id = int(movie_id)
    except (ValueError, TypeError):
        return jsonify(error="Invalid movie_id or rating value"), 400

    if not (0.5 <= rating <= 5.0):
        return jsonify(error="Rating must be between 0.5 and 5.0"), 400

    # Save to Database
    db = SessionLocal()
    try:
        existing_rating = db.query(Rating).filter(
            Rating.user_id == user_id, Rating.movie_id == movie_id
        ).first()
        if existing_rating:
            existing_rating.rating = rating
            existing_rating.timestamp = int(time.time())
        else:
            new_rating = Rating(
                user_id=user_id,
                movie_id=movie_id,
                rating=rating,
                timestamp=int(time.time()),
            )
            db.add(new_rating)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to persist rating to database: {e}")
        db.rollback()
    finally:
        db.close()

    # Update in-memory dataframe for real-time recommendations
    ratings_df: pd.DataFrame = current_app.config["ratings_df"]
    mask = (ratings_df["user_id"] == user_id) & (ratings_df["movie_id"] == movie_id)
    if mask.any():
        ratings_df = ratings_df[~mask]

    new_row = pd.DataFrame([{
        "user_id": user_id,
        "movie_id": movie_id,
        "rating": rating,
        "timestamp": int(time.time()),
    }])
    ratings_df = pd.concat([ratings_df, new_row], ignore_index=True)
    current_app.config["ratings_df"] = ratings_df

    return jsonify({
        "message": f"Rating of {rating}★ saved successfully",
        "user_id": user_id,
        "movie_id": movie_id,
        "rating": rating,
    })


@users_bp.route("/<int:user_id>/watchlist", methods=["GET"])
def get_watchlist(user_id: int):
    """Retrieve user's watchlist."""
    db = SessionLocal()
    movies_df: pd.DataFrame = current_app.config.get("movies_df")
    try:
        items = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
        movie_ids = [item.movie_id for item in items]
        if movies_df is not None and movie_ids:
            matching = movies_df[movies_df["movie_id"].isin(movie_ids)]
            return jsonify({
                "user_id": user_id,
                "watchlist": matching.to_dict(orient="records"),
                "total": len(matching)
            })
        return jsonify({"user_id": user_id, "watchlist": [], "total": 0})
    except Exception as e:
        logger.warning(f"Error fetching watchlist: {e}")
        return jsonify({"user_id": user_id, "watchlist": [], "total": 0})
    finally:
        db.close()


@users_bp.route("/<int:user_id>/watchlist", methods=["POST"])
def add_to_watchlist(user_id: int):
    """Add or toggle movie in user watchlist."""
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movie_id")
    if not movie_id:
        return jsonify(error="movie_id is required"), 400

    movie_id = int(movie_id)
    db = SessionLocal()
    try:
        existing = db.query(Watchlist).filter(
            Watchlist.user_id == user_id, Watchlist.movie_id == movie_id
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
            return jsonify({"message": "Removed from watchlist", "in_watchlist": False})
        else:
            item = Watchlist(user_id=user_id, movie_id=movie_id)
            db.add(item)
            db.commit()
            return jsonify({"message": "Added to watchlist", "in_watchlist": True})
    except Exception as e:
        db.rollback()
        logger.error(f"Watchlist error: {e}")
        return jsonify(error="Failed to update watchlist"), 500
    finally:
        db.close()
