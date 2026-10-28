"""Gestionnaire d'erreurs commun, au format du contrat :
{"error": "...", "message": "...", "details": {}}
A pousser en premier : les roles 3 et 5 en dependent.

Usage : from app.errors import ApiError
        raise ApiError(404, "not_found", "Client introuvable")
"""
import psycopg2
from psycopg2 import errors as pgerr
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status, error, message, details=None):
        super().__init__(message)
        self.status = status
        self.error = error
        self.message = message
        self.details = details or {}


def error_response(status, error, message, details=None):
    body = {"error": error, "message": message, "details": details or {}}
    return jsonify(body), status


def validation_error(message, details=None):
    return ApiError(422, "validation_error", message, details)


def not_found(message="Ressource introuvable"):
    return ApiError(404, "not_found", message)


def conflict(message):
    return ApiError(409, "conflict", message)


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(e):
        return error_response(e.status, e.error, e.message, e.details)

    @app.errorhandler(pgerr.UniqueViolation)
    def handle_unique(e):
        c = e.diag.constraint_name or "contrainte d'unicite"
        return error_response(409, "conflict", "Doublon : la ressource existe deja", {"constraint": c})

    @app.errorhandler(pgerr.ForeignKeyViolation)
    def handle_fk(e):
        return error_response(409, "conflict", "Operation impossible : des donnees liees existent (cle etrangere)")

    @app.errorhandler(pgerr.CheckViolation)
    def handle_check(e):
        return error_response(422, "validation_error", "Une contrainte de la base n'est pas respectee",
                              {"constraint": e.diag.constraint_name})

    @app.errorhandler(psycopg2.OperationalError)
    def handle_db_down(e):
        return error_response(503, "database_unavailable", "Base de donnees indisponible")

    @app.errorhandler(HTTPException)
    def handle_http(e):
        names = {400: "bad_request", 404: "not_found", 405: "method_not_allowed", 415: "unsupported_media_type"}
        return error_response(e.code, names.get(e.code, "http_error"), e.description)

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        app.logger.exception(e)
        return error_response(500, "internal_error", "Erreur interne du serveur")
