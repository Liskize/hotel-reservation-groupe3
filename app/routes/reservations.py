from datetime import datetime

from flask import Blueprint, jsonify, request

from app.crud import get_pagination, get_payload
from app.errors import ApiError, conflict, not_found, validation_error
from app.models import reservation as repo
from app.schemas.reservation_schema import STATUTS, ValidationError, validate_reservation

bp = Blueprint("reservations", __name__, url_prefix="/api/v1/reservations")


def _int_filter(name):
    raw = request.args.get(name)
    if raw is None:
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(400, "bad_request", f"{name} doit être un entier")
    if value < 1:
        raise ApiError(400, "bad_request", f"{name} doit être >= 1")
    return value


def _date_filter(name):
    raw = request.args.get(name)
    if raw is None:
        return None
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        raise ApiError(400, "bad_request", f"{name} doit être au format YYYY-MM-DD")
    return raw


def _statut_filter():
    raw = request.args.get("statut")
    if not raw:
        return None
    statut = raw.strip().upper()
    if statut not in STATUTS:
        raise ApiError(400, "bad_request", f"statut doit être parmi {sorted(STATUTS)}")
    return statut


def _prepare(res_id=None):
    """Valide le corps de la requête dans l'ordre : 400, 422, 404, 409."""
    try:
        data = validate_reservation(get_payload())
    except ValidationError as e:
        raise validation_error(e.message, e.details)
    if not repo.exists("clients", data["client_id"]):
        raise not_found(f"Client {data['client_id']} introuvable")
    if not repo.exists("hotels", data["hotel_id"]):
        raise not_found(f"Hôtel {data['hotel_id']} introuvable")
    if repo.find_duplicate(data, exclude_id=res_id):
        raise conflict("Cette réservation existe déjà")
    return data


@bp.get("")
def list_reservations():
    page, per_page = get_pagination()
    date_debut, date_fin = _date_filter("date_debut"), _date_filter("date_fin")
    if date_debut and date_fin and date_debut > date_fin:
        raise ApiError(400, "bad_request", "date_debut doit être antérieure ou égale à date_fin")
    items, total = repo.list_reservations(
        page, per_page,
        hotel_id=_int_filter("hotel_id"),
        client_id=_int_filter("client_id"),
        statut=_statut_filter(),
        date_debut=date_debut,
        date_fin=date_fin,
    )
    return jsonify({"data": items, "page": page, "per_page": per_page, "total": total})


@bp.get("/<int:res_id>")
def get_reservation(res_id):
    row = repo.get_by_id(res_id)
    if row is None:
        raise not_found(f"Réservation {res_id} introuvable")
    return jsonify(row)


@bp.post("")
def create_reservation():
    data = _prepare()
    return jsonify(repo.create(data)), 201


@bp.put("/<int:res_id>")
def update_reservation(res_id):
    if repo.get_by_id(res_id) is None:
        raise not_found(f"Réservation {res_id} introuvable")
    data = _prepare(res_id)
    return jsonify(repo.update(res_id, data))


@bp.delete("/<int:res_id>")
def delete_reservation(res_id):
    if repo.get_by_id(res_id) is None:
        raise not_found(f"Réservation {res_id} introuvable")
    repo.delete(res_id)
    return "", 204