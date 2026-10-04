"""
backend/routes/recommendations.py
Recommendation endpoints.
"""
from flask import Blueprint, jsonify, request, current_app
from src.evaluation.metrics import RecommenderMetrics

recs_bp = Blueprint("recommendations", __name__)


@recs_bp.route("/user/<int:user_id>", methods=["GET"])
def recommend_for_user(user_id: int):
    hybrid = current_app.config["hybrid"]
    top_k = int(request.args.get("top_k", 10))
    alpha = request.args.get("alpha", None)

    if alpha is not None:
        alpha = float(alpha)

    try:
        recs = hybrid.recommend(user_id, exclude_watched=True, alpha=alpha)
        if top_k != hybrid.top_k:
            recs = recs[:top_k]
    except Exception as exc:
        return jsonify(error=str(exc)), 500

    return jsonify({
        "user_id": user_id,
        "recommendations": recs,
        "alpha": alpha or hybrid.alpha,
        "count": len(recs),
    })


@recs_bp.route("/movie/<int:movie_id>", methods=["GET"])
def recommend_by_movie(movie_id: int):
    hybrid = current_app.config["hybrid"]
    top_k = int(request.args.get("top_k", 8))
    similar = hybrid.recommend_by_movie(movie_id, top_k=top_k)
    return jsonify({"movie_id": movie_id, "similar": similar})


@recs_bp.route("/evaluate", methods=["GET"])
def evaluate():
    hybrid = current_app.config["hybrid"]
    ratings_df = current_app.config["ratings_df"]
    evaluator: RecommenderMetrics = current_app.config["evaluator"]
    k = int(request.args.get("k", 10))
    n_users = int(request.args.get("n_users", 30))

    try:
        metrics = evaluator.evaluate_recommender(
            hybrid, ratings_df, k=k, n_users=n_users
        )
    except Exception as exc:
        return jsonify(error=str(exc)), 500

    return jsonify(metrics)


@recs_bp.route("/alpha", methods=["POST"])
def update_alpha():
    data = request.get_json(silent=True) or {}
    alpha = float(data.get("alpha", 0.6))
    hybrid = current_app.config["hybrid"]
    hybrid.update_alpha(alpha)
    return jsonify({"alpha": hybrid.alpha, "message": "Alpha updated"})
