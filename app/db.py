"""Connexion PostgreSQL (une par requete). Utilisable par tous les roles :
    from app.db import get_db
"""
import psycopg2
import psycopg2.extras
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            current_app.config["DATABASE_URL"],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()  # rollback implicite si pas de commit


def init_app(app):
    app.teardown_appcontext(close_db)
