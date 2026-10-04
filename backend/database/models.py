"""
backend/database/models.py
SQLAlchemy ORM Models for CineMatch.
Uses 'cm_' prefixed tables to prevent conflicts when sharing PostgreSQL databases.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base, engine


class User(Base):
    __tablename__ = "cm_users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=True)
    email = Column(String(120), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    favorite_genres = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    history = relationship("WatchHistory", back_populates="user", cascade="all, delete-orphan")


class Movie(Base):
    __tablename__ = "cm_movies"

    movie_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    year = Column(Integer, nullable=True)
    genre = Column(String(200), nullable=True, index=True)
    director = Column(String(200), nullable=True)
    cast = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    overview = Column(Text, nullable=True)
    language = Column(String(50), default="English")
    avg_rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    ratings = relationship("Rating", back_populates="movie")


class Rating(Base):
    __tablename__ = "cm_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("cm_users.user_id"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("cm_movies.movie_id"), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")


class WatchHistory(Base):
    __tablename__ = "cm_watch_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("cm_users.user_id"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("cm_movies.movie_id"), nullable=False, index=True)
    watched_at = Column(DateTime, default=datetime.utcnow)
    watch_pct = Column(Float, default=100.0)

    user = relationship("User", back_populates="history")


class Watchlist(Base):
    __tablename__ = "cm_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("cm_users.user_id"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("cm_movies.movie_id"), nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
