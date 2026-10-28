from flask import Blueprint

from app.crud import register_crud
from app.models.hotel import HOTEL_FIELDS

bp = Blueprint("hotels", __name__, url_prefix="/api/v1/hotels")
register_crud(bp, "hotels", HOTEL_FIELDS, "Hotel")
