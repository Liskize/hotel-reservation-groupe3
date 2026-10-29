from flask import Blueprint

from app.crud import register_crud
from app.models.client import CLIENT_FIELDS

bp = Blueprint("clients", __name__, url_prefix="/api/v1/clients")
register_crud(bp, "clients", CLIENT_FIELDS, "Client")
