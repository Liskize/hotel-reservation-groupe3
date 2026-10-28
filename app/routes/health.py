from flask import Blueprint, jsonify

from app.db import get_db

bp = Blueprint("health", __name__, url_prefix="/api/v1")


@bp.get("/health")
def health():
    cur = get_db().cursor()
    cur.execute("SELECT 1")
    return jsonify({"status": "ok", "database": "up"})
