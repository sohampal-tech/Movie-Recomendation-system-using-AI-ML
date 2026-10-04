"""
backend/routes/movies.py
Movie catalogue endpoints with authentic artwork poster URLs.
"""
from __future__ import annotations
from flask import Blueprint, jsonify, request, current_app
from typing import List, Dict
import pandas as pd
from src.data.fetch_posters import CURATED_POSTERS

movies_bp = Blueprint("movies", __name__)


def movies_to_list(df: pd.DataFrame) -> List[Dict]:
    records = []
    for _, row in df.iterrows():
        mid = int(row.get("movie_id", 0))
        poster = str(row.get("poster_url", "")) if pd.notna(row.get("poster_url")) else ""
        if not poster or "unsplash" in poster or len(poster) < 10:
            poster = CURATED_POSTERS.get(mid, f"https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg")

        records.append({
            "movie_id": mid,
            "title": str(row.get("title", "")),
            "year": int(row.get("year", 0)) if pd.notna(row.get("year")) else 0,
            "genre": str(row.get("genre", "")),
            "director": str(row.get("director", "")),
            "cast": str(row.get("cast", "")),
            "keywords": str(row.get("keywords", "")),
            "overview": str(row.get("overview", "")),
            "avg_rating": float(row.get("avg_rating", 0)) if pd.notna(row.get("avg_rating")) else 0.0,
            "language": str(row.get("language", "English")),
            "poster_url": poster,
        })
    return records


@movies_bp.route("/", methods=["GET"])
def list_movies():
    df: pd.DataFrame = current_app.config["movies_df"]
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    genre = request.args.get("genre", "")
    search = request.args.get("search", "").lower()
    sort_by = request.args.get("sort", "rating_desc")

    filtered = df.copy()
    if genre:
        filtered = filtered[filtered["genre"].str.contains(genre, case=False, na=False)]
    if search:
        filtered = filtered[
            filtered["title"].str.lower().str.contains(search, na=False)
            | filtered["director"].str.lower().str.contains(search, na=False)
            | filtered["cast"].str.lower().str.contains(search, na=False)
        ]

    # Sorting
    if sort_by == "rating_desc":
        filtered = filtered.sort_values("avg_rating", ascending=False)
    elif sort_by == "year_desc":
        filtered = filtered.sort_values("year", ascending=False)
    elif sort_by == "title_asc":
        filtered = filtered.sort_values("title", ascending=True)

    total = len(filtered)
    start = (page - 1) * per_page
    paginated = filtered.iloc[start: start + per_page]

    return jsonify({
        "movies": movies_to_list(paginated),
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    })


@movies_bp.route("/<int:movie_id>", methods=["GET"])
def get_movie(movie_id: int):
    df: pd.DataFrame = current_app.config["movies_df"]
    row = df[df["movie_id"] == movie_id]
    if row.empty:
        return jsonify(error="Movie not found"), 404
    return jsonify(movies_to_list(row)[0])


@movies_bp.route("/<int:movie_id>/similar", methods=["GET"])
def get_similar(movie_id: int):
    top_k = int(request.args.get("top_k", 8))
    hybrid = current_app.config["hybrid"]
    df: pd.DataFrame = current_app.config["movies_df"]
    similar = hybrid.recommend_by_movie(movie_id, top_k=top_k)
    
    # Attach poster_url to each similar movie
    for s in similar:
        smid = s.get("movie_id")
        match = df[df["movie_id"] == smid]
        if not match.empty:
            s["poster_url"] = str(match.iloc[0].get("poster_url", "")) or CURATED_POSTERS.get(smid, "")

    return jsonify({"similar": similar})


@movies_bp.route("/genres", methods=["GET"])
def list_genres():
    df: pd.DataFrame = current_app.config["movies_df"]
    genres = set()
    for g in df["genre"].dropna():
        for part in str(g).split("|"):
            genres.add(part.strip())
    return jsonify({"genres": sorted(genres)})
