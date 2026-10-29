"""Briques CRUD generiques (validation, pagination, SQL) pour hotels et clients."""
import re

from flask import current_app, jsonify, request

from app.db import get_db
from app.errors import ApiError, not_found, validation_error

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "bad_request", "Corps JSON (objet) attendu")
    return data


def validate(payload, fields):
    """fields = {nom: {"type": "str"|"int"|"email", "required": bool, "min": n, "max": n}}"""
    errors, clean = {}, {}
    for name, spec in fields.items():
        value = payload.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            if spec.get("required", True):
                errors[name] = "champ obligatoire"
            else:
                clean[name] = None
            continue
        kind = spec["type"]
        if kind in ("str", "email"):
            if not isinstance(value, str):
                errors[name] = "doit etre une chaine"
                continue
            value = value.strip()
            if kind == "email" and not EMAIL_RE.match(value):
                errors[name] = "email invalide"
                continue
            if len(value) > spec.get("max_len", 255):
                errors[name] = "trop long"
                continue
        elif kind == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                errors[name] = "doit etre un entier"
                continue
            if "min" in spec and value < spec["min"]:
                errors[name] = "doit etre >= %s" % spec["min"]
                continue
            if "max" in spec and value > spec["max"]:
                errors[name] = "doit etre <= %s" % spec["max"]
                continue
        clean[name] = value
    if errors:
        raise validation_error("Donnees invalides", errors)
    return clean


def get_pagination():
    cfg = current_app.config
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", cfg["DEFAULT_PER_PAGE"]))
    except ValueError:
        raise ApiError(400, "bad_request", "page et per_page doivent etre des entiers")
    if page < 1 or per_page < 1:
        raise ApiError(400, "bad_request", "page et per_page doivent etre >= 1")
    return page, min(per_page, cfg["MAX_PER_PAGE"])


def register_crud(bp, table, fields, label):
    cols = list(fields.keys())

    @bp.get("")
    def list_items():
        page, per_page = get_pagination()
        cur = get_db().cursor()
        cur.execute("SELECT COUNT(*) AS n FROM " + table)
        total = cur.fetchone()["n"]
        cur.execute("SELECT * FROM %s ORDER BY id LIMIT %%s OFFSET %%s" % table,
                    (per_page, (page - 1) * per_page))
        return jsonify({"data": cur.fetchall(), "page": page, "per_page": per_page, "total": total})

    @bp.get("/<int:item_id>")
    def get_item(item_id):
        cur = get_db().cursor()
        cur.execute("SELECT * FROM %s WHERE id = %%s" % table, (item_id,))
        row = cur.fetchone()
        if not row:
            raise not_found("%s %d introuvable" % (label, item_id))
        return jsonify(row)

    @bp.post("")
    def create_item():
        data = validate(get_payload(), fields)
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO %s (%s) VALUES (%s) RETURNING *"
                    % (table, ", ".join(cols), ", ".join(["%s"] * len(cols))),
                    [data[c] for c in cols])
        row = cur.fetchone()
        db.commit()
        return jsonify(row), 201

    @bp.put("/<int:item_id>")
    def update_item(item_id):
        data = validate(get_payload(), fields)
        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE %s SET %s WHERE id = %%s RETURNING *"
                    % (table, ", ".join("%s = %%s" % c for c in cols)),
                    [data[c] for c in cols] + [item_id])
        row = cur.fetchone()
        if not row:
            raise not_found("%s %d introuvable" % (label, item_id))
        db.commit()
        return jsonify(row)

    @bp.delete("/<int:item_id>")
    def delete_item(item_id):
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM %s WHERE id = %%s" % table, (item_id,))
        if cur.rowcount == 0:
            raise not_found("%s %d introuvable" % (label, item_id))
        db.commit()
        return "", 204
